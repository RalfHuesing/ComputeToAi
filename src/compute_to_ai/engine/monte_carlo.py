"""Monte-Carlo simulation and multi-path audit execution.

See Docs/01-Kern-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

import numpy as np

from compute_to_ai.engine.plan import CorrelationGroup, Plan
from compute_to_ai.engine.result import MonteCarloResult, PathAuditResult, SimulationResult


def _percentile_triplet(vals: list[float]) -> dict[int, float]:
    """Compute p10/p50/p90 of a non-empty list of values."""
    return {
        10: float(np.percentile(vals, 10)),
        50: float(np.percentile(vals, 50)),
        90: float(np.percentile(vals, 90)),
    }


def _drawn_rates_for_run(
    all_groups: dict[str, CorrelationGroup],
    group_draws: dict[str, np.ndarray],
    run_idx: int,
) -> dict[str, np.ndarray]:
    """Pick out one run's per-store rate series from the pre-drawn group draws."""
    run_drawn_rates: dict[str, np.ndarray] = {}
    for group_name, group_config in all_groups.items():
        draws = group_draws[group_name]
        for idx, store_name in enumerate(group_config.store_names):
            run_drawn_rates[store_name] = draws[run_idx, :, idx]
    return run_drawn_rates


def run_monte_carlo(plan: Plan, num_runs: int, seed: int | None = None) -> MonteCarloResult:
    """Run a Monte-Carlo simulation with stochastically drawn correlated returns."""
    from compute_to_ai.engine.simulation import (
        _default_correlation_groups,
        _pre_draw_correlated_returns,
        _run_single_simulation,
    )

    rng = np.random.default_rng(seed)
    all_groups = {**_default_correlation_groups(plan), **plan.correlation_groups}
    group_draws = _pre_draw_correlated_returns(plan, all_groups, num_runs, rng)

    raw_final_balances: list[dict[str, float]] = []
    ruin_step_counts: dict[int, int] = {}
    ruin_count = 0
    ruin_shortfalls: list[float] = []
    store_final_balances: dict[str, list[float]] = {store.name: [] for store in plan.stores}

    for run_idx in range(num_runs):
        run_drawn_rates = _drawn_rates_for_run(all_groups, group_draws, run_idx)

        final_bal, _, r_step, r_shortfall, _, _ = _run_single_simulation(plan, run_drawn_rates)
        raw_final_balances.append(final_bal)

        for name, bal in final_bal.items():
            if name in store_final_balances:
                store_final_balances[name].append(bal)

        if r_step is not None:
            ruin_count += 1
            ruin_step_counts[r_step] = ruin_step_counts.get(r_step, 0) + 1
            if r_shortfall is not None:
                ruin_shortfalls.append(r_shortfall)

    ruin_prob = ruin_count / num_runs if num_runs > 0 else 0.0
    ruin_shortfall_percentiles = _percentile_triplet(ruin_shortfalls) if ruin_shortfalls else {}

    final_percentiles: dict[str, dict[int, float]] = {
        store_name: _percentile_triplet(vals) if vals else {10: 0.0, 50: 0.0, 90: 0.0}
        for store_name, vals in store_final_balances.items()
    }

    return MonteCarloResult(
        num_runs=num_runs,
        ruin_probability=ruin_prob,
        ruin_step_distribution=ruin_step_counts,
        final_balances_percentiles=final_percentiles,
        raw_final_balances=raw_final_balances,
        ruin_shortfall_percentiles=ruin_shortfall_percentiles,
    )


def find_closest_run_to_percentile(
    raw_final_balances: list[dict[str, float]], store_names: list[str], percentile: float
) -> int:
    """Find the run index whose summed final balance is closest to requested percentile."""
    if not raw_final_balances:
        msg = "raw_final_balances must not be empty"
        raise ValueError(msg)
    sums = np.array(
        [sum(balances.get(name, 0.0) for name in store_names) for balances in raw_final_balances]
    )
    target = np.percentile(sums, percentile)
    return int(np.argmin(np.abs(sums - target)))


def run_monte_carlo_path(
    plan: Plan, run_idx: int, num_runs: int, seed: int | None = None
) -> SimulationResult:
    """Re-run one specific Monte-Carlo run index with full ledger instrumentation."""
    from compute_to_ai.engine.simulation import (
        _default_correlation_groups,
        _pre_draw_correlated_returns,
        _run_single_simulation,
    )

    rng = np.random.default_rng(seed)
    all_groups = {**_default_correlation_groups(plan), **plan.correlation_groups}
    group_draws = _pre_draw_correlated_returns(plan, all_groups, num_runs, rng)
    run_drawn_rates = _drawn_rates_for_run(all_groups, group_draws, run_idx)

    final_balances, time_series, ruin_step, ruin_shortfall, ledger, states = _run_single_simulation(
        plan, run_drawn_rates, record_ledger=True
    )
    return SimulationResult(
        final_balances=final_balances,
        time_series=time_series,
        ruin_step=ruin_step,
        ruin_shortfall=ruin_shortfall,
        ledger=ledger,
        computed_effect_final_states=states,
    )


def run_path_audit(
    plan: Plan,
    num_runs: int,
    seed: int | None = None,
    percentiles: tuple[int, ...] = (50, 10),
    store_names: list[str] | None = None,
) -> PathAuditResult:
    """Run a Monte-Carlo simulation, then re-simulate a few representative paths with ledger."""
    from compute_to_ai.engine.simulation import run_simulation

    mc_result = run_monte_carlo(plan, num_runs, seed)
    stores_for_percentile = store_names or plan.ruin_stores or [store.name for store in plan.stores]

    paths: dict[str, SimulationResult] = {}
    for percentile in percentiles:
        run_idx = find_closest_run_to_percentile(
            mc_result.raw_final_balances, stores_for_percentile, percentile
        )
        paths[f"p{percentile}"] = run_monte_carlo_path(plan, run_idx, num_runs, seed)

    paths["deterministic"] = run_simulation(plan, record_ledger=True)

    return PathAuditResult(num_runs=num_runs, paths=paths)
