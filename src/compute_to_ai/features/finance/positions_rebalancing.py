"""Positions-Rebalancing within one asset class (multiple positions sharing a
CorrelatedReturnEffect).

See Docs/04-Feature-Finanzen-Methodik.md, "Positions-Rebalancing innerhalb
einer Anlageklasse".
"""

from typing import Any

from pydantic import BaseModel

from compute_to_ai.engine.effect import ComputedEffect, register_computed_effect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.store import Store
from compute_to_ai.features.finance.position import find_positions_rebalancing_effect


class PositionsRebalancingParameters(BaseModel):
    """Parameters for the `positions_rebalancing` computed effect.

    `initial_weights` holds each non-active position's fraction of the
    group's total balance at the moment `add_position_rebalancing` was
    called - a fixed reference point, never recomputed during the
    simulation (see Docs/04, "Positions-Rebalancing innerhalb einer
    Anlageklasse").
    """

    store_names: list[str]
    active_store_name: str
    sell_threshold: float | None = None
    initial_weights: dict[str, float] = {}


def _sibling_store_names(params: PositionsRebalancingParameters) -> list[str]:
    """Every position of the group except the active one, in configured order."""
    return [name for name in params.store_names if name != params.active_store_name]


def _is_protected(store: Store) -> bool:
    """A position is Bestandsschutz-protected iff its oldest remaining lot is.

    FIFO consumption always hits the oldest lot first, so a store whose
    front lot carries `rule_version == "pre_2009"` is unavoidably
    protection-first the instant it is withdrawn from at all - checking
    only `lots[0]` (not "any lot") matches that reality (see
    Docs/04-Feature-Finanzen-Methodik.md).
    """
    return bool(store.lots) and store.lots[0].rule_version == "pre_2009"


def _unrealized_gain_fraction(store: Store) -> float:
    """Unrealized gain as a fraction of total cost basis, 0.0 if no cost basis on record."""
    total_cost_basis = sum(lot.cost_basis for lot in store.lots)
    if total_cost_basis <= 0.0:
        return 0.0
    return (store.balance - total_cost_basis) / total_cost_basis


def _rank_siblings_for_shortfall(plan: Plan, sibling_names: list[str]) -> list[str]:
    """Order siblings for shortfall cover: unprotected before protected, each
    group ascending by unrealized gain % (see Docs/04, "Verkaufspriorität").
    """

    def sort_key(name: str) -> tuple[bool, float]:
        store = plan.store(name)
        return (_is_protected(store), _unrealized_gain_fraction(store))

    return sorted(sibling_names, key=sort_key)


def _cover_active_shortfall(
    balances: dict[str, float], plan: Plan, params: PositionsRebalancingParameters
) -> None:
    """Job (a): if the active position went negative this step, draw the
    shortfall from its siblings - unprotected ones first (ascending gain %),
    protected ones only as a last resort.
    """
    active = params.active_store_name
    shortfall = -balances.get(active, 0.0)
    if shortfall <= 0.0:
        return

    ranked_siblings = _rank_siblings_for_shortfall(plan, _sibling_store_names(params))
    for name in ranked_siblings:
        if shortfall <= 0.0:
            break
        available = max(0.0, balances.get(name, 0.0))
        draw = min(shortfall, available)
        if draw <= 0.0:
            continue
        balances[name] = balances.get(name, 0.0) - draw
        balances[active] = balances.get(active, 0.0) + draw
        shortfall -= draw


def _correct_drift(
    balances: dict[str, float],
    plan: Plan,
    params: PositionsRebalancingParameters,
    sell_threshold: float,
) -> None:
    """Job (b): sell a non-active, non-protected sibling back to its initial
    weight once it drifts more than `sell_threshold` above it, investing the
    proceeds into the active position.
    """
    active = params.active_store_name
    total = sum(balances.get(name, 0.0) for name in params.store_names)
    if total <= 0.0:
        return

    for name in _sibling_store_names(params):
        initial_weight = params.initial_weights.get(name)
        if initial_weight is None or _is_protected(plan.store(name)):
            continue

        current_balance = balances.get(name, 0.0)
        current_weight = current_balance / total
        if current_weight - initial_weight <= sell_threshold:
            continue

        sell_amount = current_balance - initial_weight * total
        if sell_amount <= 0.0:
            continue
        balances[name] = current_balance - sell_amount
        balances[active] = balances.get(active, 0.0) + sell_amount


@register_computed_effect("positions_rebalancing")
def positions_rebalancing_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], _step: int, parameters: dict[str, Any], plan: Plan
) -> None:
    """Computed effect: shortfall cover (job a) plus optional threshold-triggered
    drift correction (job b) between positions of one asset class.
    """
    params = PositionsRebalancingParameters.model_validate(parameters)
    _cover_active_shortfall(balances, plan, params)
    if params.sell_threshold is not None:
        _correct_drift(balances, plan, params, params.sell_threshold)


def add_position_rebalancing(
    plan: Plan,
    store_names: list[str],
    active_store_name: str,
    sell_threshold: float | None = None,
    description: str | None = None,
) -> None:
    """Add a positions-rebalancing effect governing every position of one asset class.

    `initial_weights` (each non-active position's share of the group's
    current total balance) is captured once here, at configuration time -
    the positions must already be valued (e.g. via finance_set_asset_shares)
    or this raises.
    """
    if active_store_name not in store_names:
        msg = f"active_store_name {active_store_name!r} must be one of store_names {store_names!r}"
        raise ValueError(msg)

    plan.validate_store_names(store_names)

    new_names = set(store_names)
    if find_positions_rebalancing_effect(plan, new_names) is not None:
        msg = f"a positions_rebalancing effect already covers exactly {sorted(new_names)}"
        raise ValueError(msg)
    for effect in plan.effects:
        if isinstance(effect, ComputedEffect) and effect.function_name == "positions_rebalancing":
            overlap = set(effect.parameters.get("store_names", [])) & new_names
            if overlap:
                msg = (
                    f"store(s) {sorted(overlap)} already belong to another "
                    "positions_rebalancing effect"
                )
                raise ValueError(msg)

    total_balance = sum(plan.store(name).balance for name in store_names)
    if total_balance <= 0.0:
        msg = (
            f"cannot compute initial weights for {store_names!r}: total balance is "
            f"{total_balance!r} - value the positions first, e.g. via finance_set_asset_shares"
        )
        raise ValueError(msg)

    initial_weights = {
        name: plan.store(name).balance / total_balance
        for name in store_names
        if name != active_store_name
    }

    params = PositionsRebalancingParameters(
        store_names=store_names,
        active_store_name=active_store_name,
        sell_threshold=sell_threshold,
        initial_weights=initial_weights,
    )
    # order=5 sits between cash_bucket_manager (order=0, so this effect sees
    # the final post-sweep active-position balance for the step) and
    # capital_gains_tax_manager (order=10, so a withdrawal made here is
    # taxed the same step, see add_tax_manager's ordering rationale in tax.py).
    effect = ComputedEffect(
        name=f"Position Rebalancing {active_store_name}",
        function_name="positions_rebalancing",
        order=5,
        parameters=params.model_dump(),
        description=description,
    )
    plan.effects.append(effect)
