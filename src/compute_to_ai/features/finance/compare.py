"""Comparison of two plans configuration and simulation results.

Features include configuration delta (stores, effects, phases) and
statistical delta of Monte Carlo run outcomes.
"""

from typing import Any

from compute_to_ai.engine.effect import (
    ComputedEffect,
    CorrelatedReturnEffect,
    Effect,
    GrowingFixedEffect,
    PercentageGrowthEffect,
    TransferEffect,
)
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import MonteCarloResult


def _get_effect_key(eff: Effect) -> str:
    """Derive a key for matching effects between plans."""
    if eff.name:
        return eff.name
    store = "unknown"
    if isinstance(eff, (PercentageGrowthEffect, CorrelatedReturnEffect)):
        store = "+".join(eff.store_names)
    elif isinstance(eff, GrowingFixedEffect) or (
        isinstance(eff, ComputedEffect) and eff.store_name is not None
    ):
        store = eff.store_name
    elif isinstance(eff, TransferEffect):
        store = eff.from_store_name
    return f"{eff.type}_{store}"


def _compare_growing_fixed(
    ea: GrowingFixedEffect, eb: GrowingFixedEffect, diffs: dict[str, dict[str, Any]]
) -> None:
    if ea.store_name != eb.store_name:
        diffs["store_name"] = {"from": ea.store_name, "to": eb.store_name}
    if ea.amount_per_step != eb.amount_per_step:
        diffs["amount_per_step"] = {"from": ea.amount_per_step, "to": eb.amount_per_step}
    if ea.growth_rate != eb.growth_rate:
        diffs["growth_rate"] = {"from": ea.growth_rate, "to": eb.growth_rate}


def _compare_percentage_growth(
    ea: PercentageGrowthEffect, eb: PercentageGrowthEffect, diffs: dict[str, dict[str, Any]]
) -> None:
    if ea.store_names != eb.store_names:
        diffs["store_names"] = {"from": ea.store_names, "to": eb.store_names}
    if ea.growth_rate != eb.growth_rate:
        diffs["growth_rate"] = {"from": ea.growth_rate, "to": eb.growth_rate}


def _compare_correlated_return(
    ea: CorrelatedReturnEffect, eb: CorrelatedReturnEffect, diffs: dict[str, dict[str, Any]]
) -> None:
    if ea.store_names != eb.store_names:
        diffs["store_names"] = {"from": ea.store_names, "to": eb.store_names}
    if ea.correlation_group != eb.correlation_group:
        diffs["correlation_group"] = {"from": ea.correlation_group, "to": eb.correlation_group}
    if ea.expected_return != eb.expected_return:
        diffs["expected_return"] = {"from": ea.expected_return, "to": eb.expected_return}
    if ea.volatility != eb.volatility:
        diffs["volatility"] = {"from": ea.volatility, "to": eb.volatility}


def _compare_computed(
    ea: ComputedEffect, eb: ComputedEffect, diffs: dict[str, dict[str, Any]]
) -> None:
    if ea.store_name != eb.store_name:
        diffs["store_name"] = {"from": ea.store_name, "to": eb.store_name}
    if ea.function_name != eb.function_name:
        diffs["function_name"] = {"from": ea.function_name, "to": eb.function_name}
    if ea.parameters != eb.parameters:
        diffs["parameters"] = {"from": ea.parameters, "to": eb.parameters}
    if ea.order != eb.order:
        diffs["order"] = {"from": ea.order, "to": eb.order}


def _compare_transfer(
    ea: TransferEffect, eb: TransferEffect, diffs: dict[str, dict[str, Any]]
) -> None:
    if ea.from_store_name != eb.from_store_name:
        diffs["from_store_name"] = {"from": ea.from_store_name, "to": eb.from_store_name}
    if ea.to_store_weights != eb.to_store_weights:
        diffs["to_store_weights"] = {"from": ea.to_store_weights, "to": eb.to_store_weights}
    if ea.amount_per_step != eb.amount_per_step:
        diffs["amount_per_step"] = {"from": ea.amount_per_step, "to": eb.amount_per_step}
    if ea.growth_rate != eb.growth_rate:
        diffs["growth_rate"] = {"from": ea.growth_rate, "to": eb.growth_rate}


def _compare_base_attributes(ea: Effect, eb: Effect, diffs: dict[str, dict[str, Any]]) -> None:
    """Compare common base effect fields."""
    if ea.start_step != eb.start_step:
        diffs["start_step"] = {"from": ea.start_step, "to": eb.start_step}
    if ea.end_step != eb.end_step:
        diffs["end_step"] = {"from": ea.end_step, "to": eb.end_step}
    if ea.active_phases != eb.active_phases:
        diffs["active_phases"] = {"from": ea.active_phases, "to": eb.active_phases}
    if ea.description != eb.description:
        diffs["description"] = {"from": ea.description, "to": eb.description}


def _compare_two_effects(ea: Effect, eb: Effect, diffs: dict[str, dict[str, Any]]) -> None:
    """Compare two matched effects."""
    if ea.type != eb.type:
        diffs["type"] = {"from": ea.type, "to": eb.type}
        return

    _compare_base_attributes(ea, eb, diffs)

    if isinstance(ea, GrowingFixedEffect) and isinstance(eb, GrowingFixedEffect):
        _compare_growing_fixed(ea, eb, diffs)
    elif isinstance(ea, PercentageGrowthEffect) and isinstance(eb, PercentageGrowthEffect):
        _compare_percentage_growth(ea, eb, diffs)
    elif isinstance(ea, CorrelatedReturnEffect) and isinstance(eb, CorrelatedReturnEffect):
        _compare_correlated_return(ea, eb, diffs)
    elif isinstance(ea, ComputedEffect) and isinstance(eb, ComputedEffect):
        _compare_computed(ea, eb, diffs)
    elif isinstance(ea, TransferEffect) and isinstance(eb, TransferEffect):
        _compare_transfer(ea, eb, diffs)


def _compare_stores(
    plan_a: Plan, plan_b: Plan
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Compare stores configuration between plans."""
    stores_a = {s.name: s for s in plan_a.stores}
    stores_b = {s.name: s for s in plan_b.stores}

    added = [
        {
            "name": name,
            "balance": stores_b[name].balance,
            "description": stores_b[name].description,
        }
        for name in sorted(stores_b.keys() - stores_a.keys())
    ]

    removed = [
        {
            "name": name,
            "balance": stores_a[name].balance,
            "description": stores_a[name].description,
        }
        for name in sorted(stores_a.keys() - stores_b.keys())
    ]

    modified: list[dict[str, Any]] = []

    for name in sorted(stores_a.keys() & stores_b.keys()):
        sa, sb = stores_a[name], stores_b[name]
        diffs = {}
        if sa.balance != sb.balance:
            diffs["balance"] = {"from": sa.balance, "to": sb.balance}
        if sa.description != sb.description:
            diffs["description"] = {"from": sa.description, "to": sb.description}
        if diffs:
            modified.append({"name": name, "changes": diffs})

    return added, removed, modified


def _compare_effects(
    plan_a: Plan, plan_b: Plan
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Compare effects configuration between plans."""
    effects_a = {_get_effect_key(e): e for e in plan_a.effects}
    effects_b = {_get_effect_key(e): e for e in plan_b.effects}

    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    modified: list[dict[str, Any]] = []

    for key in sorted(effects_b.keys() - effects_a.keys()):
        eff = effects_b[key]
        added.append(
            {
                "key": key,
                "type": eff.type,
                "description": eff.description,
            }
        )

    for key in sorted(effects_a.keys() - effects_b.keys()):
        eff = effects_a[key]
        removed.append(
            {
                "key": key,
                "type": eff.type,
                "description": eff.description,
            }
        )

    for key in sorted(effects_a.keys() & effects_b.keys()):
        ea, eb = effects_a[key], effects_b[key]
        diffs: dict[str, dict[str, Any]] = {}
        _compare_two_effects(ea, eb, diffs)
        if diffs:
            modified.append(
                {
                    "key": key,
                    "type": eb.type,
                    "changes": diffs,
                }
            )

    return added, removed, modified


def _compare_phases(
    plan_a: Plan, plan_b: Plan
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Compare phases configuration between plans."""
    phases_a = {p.name: p for p in plan_a.phases}
    phases_b = {p.name: p for p in plan_b.phases}

    added = [
        {
            "name": name,
            "start_step": phases_b[name].start_step,
            "end_step": phases_b[name].end_step,
            "description": phases_b[name].description,
        }
        for name in sorted(phases_b.keys() - phases_a.keys())
    ]

    removed = [
        {
            "name": name,
            "start_step": phases_a[name].start_step,
            "end_step": phases_a[name].end_step,
            "description": phases_a[name].description,
        }
        for name in sorted(phases_a.keys() - phases_b.keys())
    ]

    modified: list[dict[str, Any]] = []

    for name in sorted(phases_a.keys() & phases_b.keys()):
        pa, pb = phases_a[name], phases_b[name]
        diffs = {}
        if pa.start_step != pb.start_step:
            diffs["start_step"] = {"from": pa.start_step, "to": pb.start_step}
        if pa.end_step != pb.end_step:
            diffs["end_step"] = {"from": pa.end_step, "to": pb.end_step}
        if pa.description != pb.description:
            diffs["description"] = {"from": pa.description, "to": pb.description}
        if diffs:
            modified.append({"name": name, "changes": diffs})

    return added, removed, modified


def _get_percentile_balances_sum(res: MonteCarloResult, stores: list[str]) -> dict[int, float]:
    sums: dict[int, float] = {}
    for p_key in [10, 50, 90]:
        val_sum = 0.0
        for st_name in stores:
            store_percents = res.final_balances_percentiles.get(st_name, {})
            val_sum += store_percents.get(p_key, 0.0)
        sums[p_key] = val_sum
    return sums


def _compare_simulation(
    plan_a: Plan,
    result_a: MonteCarloResult | None,
    plan_b: Plan,
    result_b: MonteCarloResult | None,
    warnings: list[str],
) -> dict[str, Any] | None:
    """Compare Monte Carlo outcomes of the two plans."""
    if result_a is None or result_b is None:
        warnings.append(
            "Monte Carlo results not available for both plans. "
            "Run simulation on both plans first to get outcome deltas."
        )
        return None

    target_stores_a = plan_a.ruin_stores or [s.name for s in plan_a.stores]
    target_stores_b = plan_b.ruin_stores or [s.name for s in plan_b.stores]

    pct_sums_a = _get_percentile_balances_sum(result_a, target_stores_a)
    pct_sums_b = _get_percentile_balances_sum(result_b, target_stores_b)

    return {
        "ruin_probability": {
            "from": result_a.ruin_probability,
            "to": result_b.ruin_probability,
            "diff": result_b.ruin_probability - result_a.ruin_probability,
        },
        "final_balance_percentiles": {
            p: {
                "from": pct_sums_a[p],
                "to": pct_sums_b[p],
                "diff": pct_sums_b[p] - pct_sums_a[p],
            }
            for p in [10, 50, 90]
        },
    }


def compare_plans(
    plan_a: Plan,
    result_a: MonteCarloResult | None,
    plan_b: Plan,
    result_b: MonteCarloResult | None,
) -> dict[str, Any]:
    """Compare two plans, identifying configuration changes and simulation outcome deltas."""
    warnings: list[str] = []

    # Check timelines
    if plan_a.timeline.step_count != plan_b.timeline.step_count:
        warnings.append(
            f"timeline length mismatch: {plan_a.name!r} has {plan_a.timeline.step_count} steps, "
            f"while {plan_b.name!r} has {plan_b.timeline.step_count} steps. "
            "Comparing final asset values directly might be mathematically misleading."
        )

    added_stores, removed_stores, modified_stores = _compare_stores(plan_a, plan_b)
    added_effects, removed_effects, modified_effects = _compare_effects(plan_a, plan_b)
    added_phases, removed_phases, modified_phases = _compare_phases(plan_a, plan_b)

    simulation_delta = _compare_simulation(plan_a, result_a, plan_b, result_b, warnings)

    return {
        "plan_a": plan_a.name,
        "plan_b": plan_b.name,
        "warnings": warnings,
        "config_delta": {
            "stores": {
                "added": added_stores,
                "removed": removed_stores,
                "modified": modified_stores,
            },
            "effects": {
                "added": added_effects,
                "removed": removed_effects,
                "modified": modified_effects,
            },
            "phases": {
                "added": added_phases,
                "removed": removed_phases,
                "modified": modified_phases,
            },
        },
        "simulation_delta": simulation_delta,
    }
