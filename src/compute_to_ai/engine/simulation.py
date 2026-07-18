"""SimulationRun execution - see Docs/01-Kern-Domaenenmodell.md.

A single deterministic pass or Monte-Carlo runs over the Timeline,
applying each Effect to its Store at every step.
"""

import copy

import numpy as np

from compute_to_ai.engine.effect import Effect
from compute_to_ai.engine.plan import CorrelationGroup, Plan
from compute_to_ai.engine.result import MonteCarloResult, SimulationResult
from compute_to_ai.engine.store import Store


def _calculate_phase1_updates(
    effects: list[Effect],
    t: int,
    active_phase: str | None,
    drawn_rates: dict[str, np.ndarray] | None,
    store_names: list[str],
) -> tuple[dict[str, float], dict[str, float]]:
    """Sum up fixed additions and growth rates for Phase 1 of a step."""
    fixed_additions = dict.fromkeys(store_names, 0.0)
    total_growth_rates = dict.fromkeys(store_names, 0.0)

    for effect in effects:
        if not effect.is_active(t, active_phase):
            continue

        store_name = getattr(effect, "store_name", None)
        if not isinstance(store_name, str) or store_name not in fixed_additions:
            continue

        eff_type = getattr(effect, "type", None)
        if eff_type == "growing_fixed":
            amount = getattr(effect, "amount_per_step", 0.0)
            rate = getattr(effect, "growth_rate", 0.0)
            val = amount * ((1.0 + rate) ** t)
            fixed_additions[store_name] += val
        elif eff_type == "percentage_growth":
            rate = getattr(effect, "growth_rate", 0.0)
            total_growth_rates[store_name] += rate
        elif eff_type == "correlated_return":
            if drawn_rates is not None and store_name in drawn_rates:
                rate = float(drawn_rates[store_name][t])
            else:
                rate = getattr(effect, "expected_return", 0.0)
            total_growth_rates[store_name] += rate

    return fixed_additions, total_growth_rates


def _reconcile_balances(
    sim_stores: dict[str, Store], current_balances: dict[str, float], t: int
) -> None:
    """Apply updated balances from Phase 2 back to simulated stores and lots."""
    for name, store in sim_stores.items():
        new_bal = current_balances[name]
        if new_bal != store.balance:
            diff = new_bal - store.balance
            if diff > 0:
                store.add_amount(diff, t)
            else:
                store.withdraw_amount(-diff)


def _default_correlation_groups(plan: Plan) -> dict[str, CorrelationGroup]:
    """Auto-derive an identity-matrix group for any correlation_group a
    CorrelatedReturnEffect references but that was never registered.

    Without this, a store's return would silently fall back to its
    (non-random) expected_return in _calculate_phase1_updates - a single
    unconfigured asset class would make an entire Monte-Carlo run
    deterministic instead of erroring or asking, which is far more
    dangerous than either.
    """
    referenced: dict[str, list[str]] = {}
    for effect in plan.effects:
        if getattr(effect, "type", None) != "correlated_return":
            continue
        group_name = getattr(effect, "correlation_group", "")
        if group_name in plan.correlation_groups:
            continue
        store_name = getattr(effect, "store_name", "")
        stores = referenced.setdefault(group_name, [])
        if store_name not in stores:
            stores.append(store_name)

    return {
        name: CorrelationGroup(matrix=np.eye(len(stores)).tolist(), store_names=stores)
        for name, stores in referenced.items()
    }


def _pre_draw_correlated_returns(
    plan: Plan,
    all_groups: dict[str, CorrelationGroup],
    num_runs: int,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """Pre-draw correlated return rates for each correlation group in the plan.

    Returns:
        A dict mapping group_name to np.ndarray of shape (num_runs, step_count, n_group)
    """
    step_count = plan.timeline.step_count
    group_draws: dict[str, np.ndarray] = {}

    for group_name, group_config in all_groups.items():
        n_group = len(group_config.store_names)
        means = np.zeros(n_group)
        vols = np.zeros(n_group)

        for idx, store_name in enumerate(group_config.store_names):
            effect = None
            for eff in plan.effects:
                if (
                    getattr(eff, "type", None) == "correlated_return"
                    and getattr(eff, "store_name", None) == store_name
                    and getattr(eff, "correlation_group", None) == group_name
                ):
                    effect = eff
                    break

            if effect is not None:
                means[idx] = getattr(effect, "expected_return", 0.0)
                vols[idx] = getattr(effect, "volatility", 0.0)
            else:
                msg = (
                    f"Store {store_name!r} in correlation group {group_name!r} "
                    f"has no matching CorrelatedReturnEffect in plan"
                )
                raise ValueError(msg)

        corr_matrix = np.array(group_config.matrix)
        cov = corr_matrix * vols[:, np.newaxis] * vols[np.newaxis, :]

        try:
            cholesky_matrix = np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            cov += np.eye(n_group) * 1e-9
            cholesky_matrix = np.linalg.cholesky(cov)

        z = rng.standard_normal((num_runs, step_count, n_group))
        draws = means + np.matmul(z, cholesky_matrix.T)
        group_draws[group_name] = draws

    return group_draws


def _execute_computed_effects(
    effects: list[Effect],
    sim_stores: dict[str, Store],
    t: int,
    active_phase: str | None,
    plan: Plan,
) -> None:
    """Execute computed effects and update balances and lots in sim_stores."""
    current_balances = {name: store.balance for name, store in sim_stores.items()}
    for effect in effects:
        if getattr(effect, "type", None) == "computed" and effect.is_active(t, active_phase):
            func_name = getattr(effect, "function_name", "")
            params = getattr(effect, "parameters", {})

            from compute_to_ai.engine.effect import COMPUTED_EFFECT_REGISTRY

            func = COMPUTED_EFFECT_REGISTRY.get(func_name)
            if func is None:
                msg = f"Unknown computed effect function: {func_name!r}"
                raise ValueError(msg)

            func(current_balances, t, params, plan)
            _reconcile_balances(sim_stores, current_balances, t)


def _cap_and_check_ruin(
    sim_stores: dict[str, Store], plan: Plan, t: int, ruin_step: int | None
) -> int | None:
    """Cap negative balances at 0 and return updated ruin step if applicable."""
    for store in sim_stores.values():
        if store.balance < 0.0:
            store.balance = 0.0
            store.lots = []

    if plan.ruin_stores:
        ruin_sum = sum(sim_stores[name].balance for name in plan.ruin_stores if name in sim_stores)
        if ruin_sum < plan.ruin_threshold and ruin_step is None:
            return t

    return ruin_step


def _run_single_simulation(
    plan: Plan, drawn_rates: dict[str, np.ndarray] | None = None
) -> tuple[dict[str, float], list[dict[str, float]], int | None]:
    """Execute a single simulation run.

    Returns:
        final_balances: dict of store_name -> balance
        time_series: list of dict of store_name -> balance for each step
        ruin_step: the step index where ruin first occurred, or None
    """
    sim_stores = {store.name: copy.deepcopy(store) for store in plan.stores}
    time_series: list[dict[str, float]] = []
    ruin_step: int | None = None
    store_names = list(sim_stores.keys())

    # Temporarily substitute simulation-cloned stores and effects into the plan.
    # Effects are cloned too because a ComputedEffect may use its own `parameters`
    # dict as run-scoped state (e.g. a one-time trigger flag) - without a deep
    # copy, that state would leak into every subsequent Monte-Carlo run.
    original_stores = plan.stores
    original_effects = plan.effects
    plan.stores = list(sim_stores.values())
    plan.effects = copy.deepcopy(plan.effects)

    try:
        for t in range(plan.timeline.step_count):
            active_phase = plan.get_active_phase_name(t)
            for store in sim_stores.values():
                store.withdrawn_lots_this_step = []

            # Phase 1: Growth and fixed additive effects
            fixed_additions, total_growth_rates = _calculate_phase1_updates(
                plan.effects, t, active_phase, drawn_rates, store_names
            )

            # Apply Phase 1 updates to simulated stores
            for name, store in sim_stores.items():
                if total_growth_rates[name] != 0.0:
                    store.apply_percentage_growth(total_growth_rates[name])
                if fixed_additions[name] != 0.0:
                    store.add_amount(fixed_additions[name], t)

            # Phase 2: Computed effects (registered python functions)
            _execute_computed_effects(plan.effects, sim_stores, t, active_phase, plan)

            # Cap balances at 0 and check for ruin
            ruin_step = _cap_and_check_ruin(sim_stores, plan, t, ruin_step)

            time_series.append({name: store.balance for name, store in sim_stores.items()})

    finally:
        plan.stores = original_stores
        plan.effects = original_effects

    final_balances = {name: store.balance for name, store in sim_stores.items()}
    return final_balances, time_series, ruin_step


def run_simulation(plan: Plan) -> SimulationResult:
    """Run a single deterministic simulation run."""
    final_balances, time_series, ruin_step = _run_single_simulation(plan, None)
    return SimulationResult(
        final_balances=final_balances, time_series=time_series, ruin_step=ruin_step
    )


def run_monte_carlo(plan: Plan, num_runs: int, seed: int | None = None) -> MonteCarloResult:
    """Run a Monte-Carlo simulation with stochastically drawn correlated returns."""
    rng = np.random.default_rng(seed)
    all_groups = {**_default_correlation_groups(plan), **plan.correlation_groups}
    group_draws = _pre_draw_correlated_returns(plan, all_groups, num_runs, rng)

    raw_final_balances: list[dict[str, float]] = []
    ruin_step_counts: dict[int, int] = {}
    ruin_count = 0
    store_final_balances: dict[str, list[float]] = {store.name: [] for store in plan.stores}

    for run_idx in range(num_runs):
        run_drawn_rates: dict[str, np.ndarray] = {}
        for group_name, group_config in all_groups.items():
            draws = group_draws[group_name]
            for idx, store_name in enumerate(group_config.store_names):
                run_drawn_rates[store_name] = draws[run_idx, :, idx]

        final_bal, _, r_step = _run_single_simulation(plan, run_drawn_rates)
        raw_final_balances.append(final_bal)

        for name, bal in final_bal.items():
            if name in store_final_balances:
                store_final_balances[name].append(bal)

        if r_step is not None:
            ruin_count += 1
            ruin_step_counts[r_step] = ruin_step_counts.get(r_step, 0) + 1

    ruin_prob = ruin_count / num_runs if num_runs > 0 else 0.0

    final_percentiles: dict[str, dict[int, float]] = {}
    for store_name, vals in store_final_balances.items():
        if vals:
            p10 = float(np.percentile(vals, 10))
            p50 = float(np.percentile(vals, 50))
            p90 = float(np.percentile(vals, 90))
            final_percentiles[store_name] = {10: p10, 50: p50, 90: p90}
        else:
            final_percentiles[store_name] = {10: 0.0, 50: 0.0, 90: 0.0}

    return MonteCarloResult(
        num_runs=num_runs,
        ruin_probability=ruin_prob,
        ruin_step_distribution=ruin_step_counts,
        final_balances_percentiles=final_percentiles,
        raw_final_balances=raw_final_balances,
    )
