"""Phase 1 simulation effect calculations.

Transfer, growing fixed, percentage growth, and correlated return effects.
See Docs/01-Kern-Domaenenmodell.md.
"""

from typing import TYPE_CHECKING

import numpy as np

from compute_to_ai.engine.effect import (
    CorrelatedReturnEffect,
    Effect,
    GrowingFixedEffect,
    PercentageGrowthEffect,
    TransferEffect,
)
from compute_to_ai.engine.result import LedgerEffectType, LedgerEntry

if TYPE_CHECKING:
    from compute_to_ai.engine.plan import Plan


def _resolve_rate(plan: "Plan | None", rate: float | str) -> float:
    """Helper to resolve a rate value as float or via plan parameter reference."""
    if plan is not None:
        return plan.resolve_rate(rate)
    if isinstance(rate, str) and rate.startswith("ref:"):
        msg = f"Cannot resolve parameter reference {rate!r} without a Plan instance."
        raise ValueError(msg)
    return float(rate)


def _ledger_entry(
    effect: Effect, eff_type: LedgerEffectType, t: int, store_name: str, delta: float
) -> LedgerEntry:
    """Build a LedgerEntry for one Effect's contribution to one Store this step."""
    return LedgerEntry(
        step=t,
        effect_name=effect.name if effect.name is not None else eff_type,
        effect_type=eff_type,
        function_name=effect.function_name if hasattr(effect, "function_name") else None,
        store_name=store_name,
        delta=delta,
    )


def _record_ledger_entry(
    ledger: list[LedgerEntry] | None,
    effect: Effect,
    eff_type: LedgerEffectType,
    t: int,
    store_name: str,
    delta: float,
) -> None:
    if ledger is not None and delta != 0.0:
        ledger.append(_ledger_entry(effect, eff_type, t, store_name, delta))


def _apply_transfer_effect(
    effect: TransferEffect,
    t: int,
    fixed_additions: dict[str, float],
    ledger: list[LedgerEntry] | None = None,
    plan: "Plan | None" = None,
) -> None:
    from_name = effect.from_store_name
    amount = effect.amount_per_step
    rate = _resolve_rate(plan, effect.growth_rate)
    val = amount * ((1.0 + rate) ** t)
    if from_name in fixed_additions:
        fixed_additions[from_name] -= val
        _record_ledger_entry(ledger, effect, "transfer", t, from_name, -val)
    for to_name, weight in effect.to_store_weights.items():
        if to_name in fixed_additions:
            contribution = val * weight
            fixed_additions[to_name] += contribution
            _record_ledger_entry(ledger, effect, "transfer", t, to_name, contribution)


def _apply_growing_fixed_effect(
    effect: GrowingFixedEffect,
    t: int,
    fixed_additions: dict[str, float],
    ledger: list[LedgerEntry] | None,
    plan: "Plan | None" = None,
) -> None:
    store_name = effect.store_name
    if store_name in fixed_additions:
        amount = effect.amount_per_step
        rate = _resolve_rate(plan, effect.growth_rate)
        val = amount * ((1.0 + rate) ** t)
        fixed_additions[store_name] += val
        _record_ledger_entry(ledger, effect, "growing_fixed", t, store_name, val)


def _apply_growth_rate_to_stores(
    effect: PercentageGrowthEffect | CorrelatedReturnEffect,
    eff_type: LedgerEffectType,
    rate: float,
    t: int,
    store_balances: dict[str, float],
    fixed_additions: dict[str, float],
    total_growth_rates: dict[str, float],
    ledger: list[LedgerEntry] | None,
) -> None:
    for store_name in effect.store_names:
        if store_name in fixed_additions:
            total_growth_rates[store_name] += rate
            _record_ledger_entry(
                ledger,
                effect,
                eff_type,
                t,
                store_name,
                store_balances.get(store_name, 0.0) * rate,
            )


def _apply_phase1_effect(
    effect: Effect,
    t: int,
    drawn_rates: dict[str, np.ndarray] | None,
    store_balances: dict[str, float],
    fixed_additions: dict[str, float],
    total_growth_rates: dict[str, float],
    ledger: list[LedgerEntry] | None = None,
    plan: "Plan | None" = None,
) -> None:
    if isinstance(effect, TransferEffect):
        _apply_transfer_effect(effect, t, fixed_additions, ledger, plan=plan)
    elif isinstance(effect, GrowingFixedEffect):
        _apply_growing_fixed_effect(effect, t, fixed_additions, ledger, plan=plan)
    elif isinstance(effect, PercentageGrowthEffect):
        rate = _resolve_rate(plan, effect.growth_rate)
        _apply_growth_rate_to_stores(
            effect,
            "percentage_growth",
            rate,
            t,
            store_balances,
            fixed_additions,
            total_growth_rates,
            ledger,
        )
    elif isinstance(effect, CorrelatedReturnEffect):
        axis_name = effect.store_names[0]
        if drawn_rates is not None and axis_name in drawn_rates:
            rate = float(drawn_rates[axis_name][t])
        else:
            rate = effect.expected_return
        _apply_growth_rate_to_stores(
            effect,
            "correlated_return",
            rate,
            t,
            store_balances,
            fixed_additions,
            total_growth_rates,
            ledger,
        )


def _calculate_phase1_updates(
    effects: list[Effect],
    t: int,
    active_phase: str | None,
    drawn_rates: dict[str, np.ndarray] | None,
    store_names: list[str],
    store_balances: dict[str, float],
    ledger: list[LedgerEntry] | None = None,
    plan: "Plan | None" = None,
) -> tuple[dict[str, float], dict[str, float]]:
    """Accumulate all Phase 1 effects into per-store fixed additions and total growth rates."""
    fixed_additions = dict.fromkeys(store_names, 0.0)
    total_growth_rates = dict.fromkeys(store_names, 0.0)

    for effect in effects:
        if not effect.is_active(t, active_phase):
            continue
        _apply_phase1_effect(
            effect,
            t,
            drawn_rates,
            store_balances,
            fixed_additions,
            total_growth_rates,
            ledger,
            plan=plan,
        )

    return fixed_additions, total_growth_rates
