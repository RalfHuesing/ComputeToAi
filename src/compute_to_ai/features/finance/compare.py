"""Comparison of two plans configuration and simulation results.

Features include configuration delta (stores, effects, phases) and
statistical delta of Monte Carlo run outcomes.
"""

from typing import Any
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import MonteCarloResult


def compare_plans(
    plan_a: Plan,
    result_a: MonteCarloResult | None,
    plan_b: Plan,
    result_b: MonteCarloResult | None,
) -> dict[str, Any]:
    """Compare two plans, identifying configuration changes and simulation outcome deltas."""
    warnings = []

    # Check timelines
    if plan_a.timeline.step_count != plan_b.timeline.step_count:
        warnings.append(
            f"timeline length mismatch: {plan_a.name!r} has {plan_a.timeline.step_count} steps, "
            f"while {plan_b.name!r} has {plan_b.timeline.step_count} steps. "
            "Comparing final asset values directly might be mathematically misleading."
        )

    # 1. Compare Stores
    stores_a = {s.name: s for s in plan_a.stores}
    stores_b = {s.name: s for s in plan_b.stores}

    added_stores = []
    removed_stores = []
    modified_stores = []

    for name in sorted(stores_b.keys() - stores_a.keys()):
        added_stores.append({
            "name": name,
            "balance": stores_b[name].balance,
            "description": stores_b[name].description,
        })

    for name in sorted(stores_a.keys() - stores_b.keys()):
        removed_stores.append({
            "name": name,
            "balance": stores_a[name].balance,
            "description": stores_a[name].description,
        })

    for name in sorted(stores_a.keys() & stores_b.keys()):
        sa, sb = stores_a[name], stores_b[name]
        diffs = {}
        if sa.balance != sb.balance:
            diffs["balance"] = {"from": sa.balance, "to": sb.balance}
        if sa.description != sb.description:
            diffs["description"] = {"from": sa.description, "to": sb.description}
        if diffs:
            modified_stores.append({"name": name, "changes": diffs})

    # 2. Compare Effects
    # Match effects by name. If name is missing, use store_name + type as key.
    def get_effect_key(eff: Any) -> str:
        if getattr(eff, "name", None):
            return eff.name
        # Fallback key construction
        store = getattr(eff, "store_name", "unknown")
        eff_type = getattr(eff, "type", "unknown")
        return f"{eff_type}_{store}"

    effects_a = {get_effect_key(e): e for e in plan_a.effects}
    effects_b = {get_effect_key(e): e for e in plan_b.effects}

    added_effects = []
    removed_effects = []
    modified_effects = []

    for key in sorted(effects_b.keys() - effects_a.keys()):
        eff = effects_b[key]
        added_effects.append({
            "key": key,
            "type": getattr(eff, "type", "unknown"),
            "description": getattr(eff, "description", None),
        })

    for key in sorted(effects_a.keys() - effects_b.keys()):
        eff = effects_a[key]
        removed_effects.append({
            "key": key,
            "type": getattr(eff, "type", "unknown"),
            "description": getattr(eff, "description", None),
        })

    for key in sorted(effects_a.keys() & effects_b.keys()):
        ea, eb = effects_a[key], effects_b[key]
        diffs = {}
        # Attributes to compare
        attrs = [
            "amount_per_step",
            "growth_rate",
            "inflation_rate",
            "start_step",
            "end_step",
            "active_phases",
            "expected_return",
            "volatility",
            "description",
        ]
        for attr in attrs:
            val_a = getattr(ea, attr, None)
            val_b = getattr(eb, attr, None)
            if val_a != val_b:
                diffs[attr] = {"from": val_a, "to": val_b}

        # Compare parameters for computed effects
        params_a = getattr(ea, "parameters", None)
        params_b = getattr(eb, "parameters", None)
        if params_a != params_b:
            diffs["parameters"] = {"from": params_a, "to": params_b}

        if diffs:
            modified_effects.append({
                "key": key,
                "type": getattr(eb, "type", "unknown"),
                "changes": diffs,
            })

    # 3. Compare Phases
    phases_a = {p.name: p for p in plan_a.phases}
    phases_b = {p.name: p for p in plan_b.phases}

    added_phases = []
    removed_phases = []
    modified_phases = []

    for name in sorted(phases_b.keys() - phases_a.keys()):
        added_phases.append({
            "name": name,
            "start_step": phases_b[name].start_step,
            "end_step": phases_b[name].end_step,
            "description": phases_b[name].description,
        })

    for name in sorted(phases_a.keys() - phases_b.keys()):
        removed_phases.append({
            "name": name,
            "start_step": phases_a[name].start_step,
            "end_step": phases_a[name].end_step,
            "description": phases_a[name].description,
        })

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
            modified_phases.append({"name": name, "changes": diffs})

    # 4. Compare Monte Carlo simulation outcomes
    simulation_delta = None
    if result_a is not None and result_b is not None:
        # Sum of percentiles across target-condition stores (ruin_stores)
        target_stores_a = plan_a.ruin_stores or [s.name for s in plan_a.stores]
        target_stores_b = plan_b.ruin_stores or [s.name for s in plan_b.stores]

        # Extract percentile final balances sum
        def get_percentile_balances_sum(res: MonteCarloResult, stores: list[str]) -> dict[int, float]:
            sums = {}
            for p_key in [10, 50, 90]:
                val_sum = 0.0
                for st_name in stores:
                    store_percents = res.final_balances_percentiles.get(st_name, {})
                    val_sum += store_percents.get(p_key, 0.0)
                sums[p_key] = val_sum
            return sums

        pct_sums_a = get_percentile_balances_sum(result_a, target_stores_a)
        pct_sums_b = get_percentile_balances_sum(result_b, target_stores_b)

        simulation_delta = {
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
    else:
        warnings.append(
            "Monte Carlo results not available for both plans. Run simulation on both plans first to get outcome deltas."
        )

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
