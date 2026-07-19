"""Portfolio and asset classes management (rebalancing, asset allocation).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

from pydantic import BaseModel

from compute_to_ai.engine.effect import (
    ComputedEffect,
    CorrelatedReturnEffect,
    register_computed_effect,
)
from compute_to_ai.engine.plan import CorrelationGroup, Plan
from compute_to_ai.engine.store import Lot, Store


class PortfolioRebalancingParameters(BaseModel):
    """Parameters for the `portfolio_rebalancing` computed effect."""

    weights: dict[str, float]


@register_computed_effect("portfolio_rebalancing")
def portfolio_rebalancing_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], _step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    """Computed effect to rebalance asset classes to match target weights."""
    params = PortfolioRebalancingParameters.model_validate(parameters)

    total_value = sum(balances.get(name, 0.0) for name in params.weights)
    if total_value <= 0.0:
        return

    for name, weight in params.weights.items():
        balances[name] = total_value * weight


def add_asset_class(
    plan: Plan,
    store_name: str,
    initial_balance: float,
    expected_return: float,
    volatility: float,
    correlation_group: str = "portfolio",
    description: str | None = None,
) -> None:
    """Add an asset class with a correlated return effect to the plan."""
    # Ensure the store exists and has lot tracking enabled
    store_exists = False
    for st in plan.stores:
        if st.name == store_name:
            store_exists = True
            break
    if not store_exists:
        plan.stores.append(
            Store(
                name=store_name,
                balance=initial_balance,
                lots=[
                    Lot(
                        quantity=initial_balance,
                        created_step=0,
                        cost_basis=initial_balance,
                    )
                ],
                description=description,
            )
        )

    # Add the CorrelatedReturnEffect
    effect = CorrelatedReturnEffect(
        name=f"Rendite {store_name}",
        store_name=store_name,
        expected_return=expected_return,
        volatility=volatility,
        correlation_group=correlation_group,
        description=description,
    )
    plan.effects.append(effect)


def set_correlation_matrix(
    plan: Plan, group_name: str, matrix: list[list[float]], store_names: list[str]
) -> None:
    """Set the correlation matrix and matching store names for a named correlation group."""
    plan.correlation_groups[group_name] = CorrelationGroup(matrix=matrix, store_names=store_names)


def add_portfolio_rebalancing(
    plan: Plan,
    name: str,
    weights: dict[str, float],
    start_step: int = 0,
    end_step: int | None = None,
    description: str | None = None,
) -> None:
    """Add a computed rebalancing effect to the plan."""
    params = PortfolioRebalancingParameters(weights=weights)
    effect = ComputedEffect(
        name=name,
        function_name="portfolio_rebalancing",
        start_step=start_step,
        end_step=end_step,
        parameters=params.model_dump(),
        description=description,
    )
    plan.effects.append(effect)


class CashBucketParameters(BaseModel):
    """Parameters for the `cash_bucket_manager` computed effect.

    Both `add_cash_bucket` (writer) and `cash_bucket_manager_func` (reader)
    validate through this single model instead of matching dict-key strings
    by convention, so a typo becomes a validation error instead of a
    silently ignored default.
    """

    cash_store_name: str = "cash"
    portfolio_weights: dict[str, float]
    emergency_buffer_months: dict[str, float]
    monthly_expenses: float
    inflation_rate: float = 0.0
    near_horizon_steps: int = 2
    withdrawal_years: float = 3.0
    withdrawal_phase_names: list[str] = []
    max_target_cash: float | None = None


def _calculate_near_horizon_outlook(
    plan: Plan, cash_store: str, step: int, near_horizon_steps: int
) -> float:
    """Calculate the near-horizon component (upcoming expenses)."""
    buffer_2 = 0.0
    end_s = min(step + 1 + near_horizon_steps, plan.timeline.step_count)
    for s in range(step + 1, end_s):
        s_phase = plan.get_active_phase_name(s)
        for effect in plan.effects:
            if effect.is_active(s, s_phase) and getattr(effect, "store_name", None) == cash_store:
                amount = getattr(effect, "amount_per_step", 0.0)
                if amount < 0.0:
                    rate = getattr(effect, "growth_rate", 0.0)
                    buffer_2 += -amount * ((1.0 + rate) ** s)
    return buffer_2


def _calculate_withdrawal_buffer(
    plan: Plan,
    cash_store: str,
    step: int,
    active_phase: str | None,
    withdrawal_years: float,
    withdrawal_phase_names: list[str],
) -> float:
    """Calculate the withdrawal buffer component (Entnahmepuffer, retirement gap buffer).

    Which phases count towards this buffer is decided solely by the explicit
    `withdrawal_phase_names` parameter, never by inspecting a phase's name -
    a Phase's name is an opaque label (see Docs/01-Kern-Domaenenmodell.md).
    """
    if active_phase is None or active_phase not in withdrawal_phase_names:
        return 0.0

    e_val = 0.0
    i_val = 0.0
    for effect in plan.effects:
        if (
            effect.is_active(step, active_phase)
            and getattr(effect, "store_name", None) == cash_store
        ):
            amount = getattr(effect, "amount_per_step", 0.0)
            rate = getattr(effect, "growth_rate", 0.0)
            val = amount * ((1.0 + rate) ** step)
            if val < 0.0:
                e_val += -val
            else:
                i_val += val

    if e_val > 0.0:
        dependency = max(0.0, (e_val - i_val) / e_val)
        return withdrawal_years * dependency * e_val
    return 0.0


@register_computed_effect("cash_bucket_manager")
def cash_bucket_manager_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], step: int, parameters: dict[str, Any], plan: Plan
) -> None:
    """Computed effect to manage Cash-Bucket target sizes and portfolio rebalancing."""
    params = CashBucketParameters.model_validate(parameters)
    cash_store = params.cash_store_name
    active_phase = plan.get_active_phase_name(step)

    # 1. Einkommensausfallpuffer
    months = params.emergency_buffer_months.get(active_phase or "", 0.0)
    monthly_expenses_inflated = params.monthly_expenses * ((1.0 + params.inflation_rate) ** step)
    buffer_1 = months * monthly_expenses_inflated

    # 2. Nahsicht-Komponente
    buffer_2 = _calculate_near_horizon_outlook(plan, cash_store, step, params.near_horizon_steps)

    # 3. Entnahmepuffer
    buffer_3 = _calculate_withdrawal_buffer(
        plan,
        cash_store,
        step,
        active_phase,
        params.withdrawal_years,
        params.withdrawal_phase_names,
    )

    # Target Cash-Bucket size
    target_cash = buffer_1 + buffer_2 + buffer_3
    if params.max_target_cash is not None:
        target_cash = min(target_cash, params.max_target_cash)
    current_cash = balances.get(cash_store, 0.0)
    portfolio_weights = params.portfolio_weights

    if current_cash > target_cash:
        # Excess cash: move to portfolio
        excess = current_cash - target_cash
        balances[cash_store] = target_cash
        for name, weight in portfolio_weights.items():
            balances[name] = balances.get(name, 0.0) + excess * weight
    elif current_cash < target_cash:
        # Deficit: withdraw from portfolio
        deficit = target_cash - current_cash
        total_portfolio = sum(balances.get(name, 0.0) for name in portfolio_weights)
        if total_portfolio >= deficit:
            balances[cash_store] = target_cash
            for name, weight in portfolio_weights.items():
                balances[name] = balances.get(name, 0.0) - deficit * weight
        else:
            # Withdraw everything
            balances[cash_store] = current_cash + total_portfolio
            for name in portfolio_weights:
                balances[name] = 0.0


def add_cash_bucket(
    plan: Plan,
    portfolio_weights: dict[str, float],
    emergency_buffer_months: dict[str, float],
    monthly_expenses: float,
    inflation_rate: float = 0.0,
    near_horizon_steps: int = 2,
    withdrawal_years: float = 3.0,
    cash_store_name: str = "cash",
    withdrawal_phase_names: list[str] | None = None,
    max_target_cash: float | None = None,
    description: str | None = None,
) -> None:
    """Add a computed cash bucket manager to the plan.

    `withdrawal_phase_names` names the phases (e.g. the retirement phase)
    whose withdrawal dependency feeds the Entnahmepuffer component; phases
    not listed there never contribute to it, regardless of how they're named.

    `max_target_cash` caps the otherwise unbounded, dynamically computed
    target size - without it, any cash above the computed target is always
    swept into the portfolio in full, with no way to let it accumulate
    beyond that target.
    """
    # Ensure the cash store exists
    store_exists = False
    for st in plan.stores:
        if st.name == cash_store_name:
            store_exists = True
            break
    if not store_exists:
        plan.stores.append(Store(name=cash_store_name, balance=0.0, description=description))

    params = CashBucketParameters(
        cash_store_name=cash_store_name,
        portfolio_weights=portfolio_weights,
        emergency_buffer_months=emergency_buffer_months,
        monthly_expenses=monthly_expenses,
        inflation_rate=inflation_rate,
        near_horizon_steps=near_horizon_steps,
        withdrawal_years=withdrawal_years,
        withdrawal_phase_names=withdrawal_phase_names or [],
        max_target_cash=max_target_cash,
    )

    effect = ComputedEffect(
        name="Cash Bucket Manager",
        function_name="cash_bucket_manager",
        order=0,  # runs between pension tax (-10) and capital gains tax (10), see tax.py
        parameters=params.model_dump(),
        description=description,
    )
    plan.effects.append(effect)
