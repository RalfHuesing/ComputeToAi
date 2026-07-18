"""Portfolio and asset classes management (rebalancing, asset allocation).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

from compute_to_ai.engine.effect import (
    ComputedEffect,
    CorrelatedReturnEffect,
    register_computed_effect,
)
from compute_to_ai.engine.plan import CorrelationGroup, Plan
from compute_to_ai.engine.store import Lot, Store


@register_computed_effect("portfolio_rebalancing")
def portfolio_rebalancing_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], _step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    """Computed effect to rebalance asset classes to match target weights."""
    weights = {k: float(v) for k, v in parameters["weights"].items()}

    total_value = sum(balances.get(name, 0.0) for name in weights)
    if total_value <= 0.0:
        return

    for name, weight in weights.items():
        balances[name] = total_value * weight


def add_asset_class(
    plan: Plan,
    store_name: str,
    initial_balance: float,
    expected_return: float,
    volatility: float,
    correlation_group: str = "portfolio",
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
                lots=[Lot(quantity=initial_balance, created_step=0)],
            )
        )

    # Add the CorrelatedReturnEffect
    effect = CorrelatedReturnEffect(
        name=f"Rendite {store_name}",
        store_name=store_name,
        expected_return=expected_return,
        volatility=volatility,
        correlation_group=correlation_group,
    )
    plan.effects.append(effect)


def set_correlation_matrix(
    plan: Plan, group_name: str, matrix: list[list[float]], store_names: list[str]
) -> None:
    """Set the correlation matrix and matching store names for a named correlation group."""
    plan.correlation_groups[group_name] = CorrelationGroup(
        matrix=matrix, store_names=store_names
    )


def add_portfolio_rebalancing(
    plan: Plan,
    name: str,
    weights: dict[str, float],
    start_step: int = 0,
    end_step: int | None = None,
) -> None:
    """Add a computed rebalancing effect to the plan."""
    effect = ComputedEffect(
        name=name,
        function_name="portfolio_rebalancing",
        start_step=start_step,
        end_step=end_step,
        parameters={"weights": weights},
    )
    plan.effects.append(effect)
