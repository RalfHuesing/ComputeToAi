"""SimulationRun execution - see Docs/01-Kern-Domaenenmodell.md.

A single deterministic pass or Monte-Carlo runs over the Timeline,
applying each Effect to its Store at every step.
"""

import copy

import numpy as np

from compute_to_ai.engine.effect import Effect
from compute_to_ai.engine.plan import CorrelationGroup, Plan
from compute_to_ai.engine.result import (
    ComputedEffectFinalState,
    LedgerEffectType,
    LedgerEntry,
    MonteCarloResult,
    PathAuditResult,
    SimulationResult,
)
from compute_to_ai.engine.store import Store


def _ledger_entry(
    effect: Effect, eff_type: LedgerEffectType, t: int, store_name: str, delta: float
) -> LedgerEntry:
    """Build a LedgerEntry for one Effect's contribution to one Store this step."""
    return LedgerEntry(
        step=t,
        effect_name=effect.name if effect.name is not None else eff_type,
        effect_type=eff_type,
        function_name=getattr(effect, "function_name", None),
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
    """Append a LedgerEntry if a ledger is being recorded and the delta is nonzero.

    Mirrors the `if diff != 0.0` guard already used for computed effects in
    `_execute_computed_effects`, so an active-but-currently-zero effect (e.g.
    a 0% interest rate) doesn't clutter the ledger with no-op entries.
    """
    if ledger is not None and delta != 0.0:
        ledger.append(_ledger_entry(effect, eff_type, t, store_name, delta))


def _apply_transfer_effect(
    effect: Effect,
    t: int,
    fixed_additions: dict[str, float],
    ledger: list[LedgerEntry] | None = None,
) -> None:
    """Add a TransferEffect's per-step contribution to `fixed_additions` in place."""
    from_name = getattr(effect, "from_store_name", None)
    amount = getattr(effect, "amount_per_step", 0.0)
    rate = getattr(effect, "growth_rate", 0.0)
    val = amount * ((1.0 + rate) ** t)
    if isinstance(from_name, str) and from_name in fixed_additions:
        fixed_additions[from_name] -= val
        _record_ledger_entry(ledger, effect, "transfer", t, from_name, -val)
    for to_name, weight in getattr(effect, "to_store_weights", {}).items():
        if to_name in fixed_additions:
            contribution = val * weight
            fixed_additions[to_name] += contribution
            _record_ledger_entry(ledger, effect, "transfer", t, to_name, contribution)


def _calculate_phase1_updates(
    effects: list[Effect],
    t: int,
    active_phase: str | None,
    drawn_rates: dict[str, np.ndarray] | None,
    store_names: list[str],
    store_balances: dict[str, float],
    ledger: list[LedgerEntry] | None = None,
) -> tuple[dict[str, float], dict[str, float]]:
    """Sum up fixed additions and growth rates for Phase 1 of a step."""
    fixed_additions = dict.fromkeys(store_names, 0.0)
    total_growth_rates = dict.fromkeys(store_names, 0.0)

    for effect in effects:
        if not effect.is_active(t, active_phase):
            continue

        eff_type = getattr(effect, "type", None)
        if eff_type == "transfer":
            _apply_transfer_effect(effect, t, fixed_additions, ledger)
            continue

        store_name = getattr(effect, "store_name", None)
        if not isinstance(store_name, str) or store_name not in fixed_additions:
            continue

        if eff_type == "growing_fixed":
            amount = getattr(effect, "amount_per_step", 0.0)
            rate = getattr(effect, "growth_rate", 0.0)
            val = amount * ((1.0 + rate) ** t)
            fixed_additions[store_name] += val
            _record_ledger_entry(ledger, effect, eff_type, t, store_name, val)
        elif eff_type == "percentage_growth":
            rate = getattr(effect, "growth_rate", 0.0)
            total_growth_rates[store_name] += rate
            _record_ledger_entry(
                ledger, effect, eff_type, t, store_name, store_balances.get(store_name, 0.0) * rate
            )
        elif eff_type == "correlated_return":
            if drawn_rates is not None and store_name in drawn_rates:
                rate = float(drawn_rates[store_name][t])
            else:
                rate = getattr(effect, "expected_return", 0.0)
            total_growth_rates[store_name] += rate
            _record_ledger_entry(
                ledger, effect, eff_type, t, store_name, store_balances.get(store_name, 0.0) * rate
            )

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
    ledger: list[LedgerEntry] | None = None,
) -> None:
    """Execute computed effects (sorted by `order`) and update balances/lots in sim_stores."""
    current_balances = {name: store.balance for name, store in sim_stores.items()}
    computed = [e for e in effects if getattr(e, "type", None) == "computed"]
    for effect in sorted(computed, key=lambda e: getattr(e, "order", 0)):
        if effect.is_active(t, active_phase):
            func_name = getattr(effect, "function_name", "")
            params = getattr(effect, "parameters", {})

            from compute_to_ai.engine.effect import COMPUTED_EFFECT_REGISTRY

            func = COMPUTED_EFFECT_REGISTRY.get(func_name)
            if func is None:
                msg = f"Unknown computed effect function: {func_name!r}"
                raise ValueError(msg)

            # A computed effect's economic footprint is the diff it leaves
            # on `current_balances` - the same mechanism the engine already
            # uses to apply it, reused here to attribute a ledger delta
            # without the engine needing to understand what the effect does.
            before = dict(current_balances) if ledger is not None else None
            func(current_balances, t, params, plan)
            _reconcile_balances(sim_stores, current_balances, t)

            if ledger is not None and before is not None:
                for name, value in current_balances.items():
                    diff = value - before.get(name, 0.0)
                    if diff != 0.0:
                        ledger.append(_ledger_entry(effect, "computed", t, name, diff))


def _cap_and_check_ruin(
    sim_stores: dict[str, Store],
    plan: Plan,
    t: int,
    ruin_step: int | None,
    ruin_shortfall: float | None,
) -> tuple[int | None, float | None]:
    """Check ruin against the pre-cap balances, then cap negative balances at 0.

    The ruin-stores sum is evaluated before capping so that a
    `ruin_threshold` of 0.0 (the default) can still detect a run that went
    negative - capped balances are never below 0.0, so checking after
    capping can never trigger ruin at the default threshold.
    """
    if plan.ruin_stores and ruin_step is None:
        uncapped_sum = sum(
            sim_stores[name].balance for name in plan.ruin_stores if name in sim_stores
        )
        if uncapped_sum < plan.ruin_threshold:
            ruin_step = t
            ruin_shortfall = plan.ruin_threshold - uncapped_sum

    for store in sim_stores.values():
        if store.balance < 0.0:
            store.balance = 0.0
            store.lots = []

    return ruin_step, ruin_shortfall


def _collect_computed_effect_final_states(effects: list[Effect]) -> list[ComputedEffectFinalState]:
    """Snapshot every ComputedEffect's post-run `parameters` state.

    Called on the run-scoped, deep-copied effects list before it is
    discarded, so run-scoped mutable state (e.g. a one-time trigger flag) is
    not lost together with the clone (see Docs/01-Kern-Domaenenmodell.md,
    "Ledger").
    """
    states: list[ComputedEffectFinalState] = []
    for effect in effects:
        if getattr(effect, "type", None) != "computed":
            continue
        func_name = getattr(effect, "function_name", "")
        states.append(
            ComputedEffectFinalState(
                effect_name=effect.name if effect.name is not None else func_name,
                function_name=func_name,
                parameters=dict(getattr(effect, "parameters", {})),
            )
        )
    return states


def _run_single_simulation(
    plan: Plan,
    drawn_rates: dict[str, np.ndarray] | None = None,
    record_ledger: bool = False,
) -> tuple[
    dict[str, float],
    list[dict[str, float]],
    int | None,
    float | None,
    list[LedgerEntry],
    list[ComputedEffectFinalState],
]:
    """Execute a single simulation run.

    Returns:
        final_balances: dict of store_name -> balance
        time_series: list of dict of store_name -> balance for each step
        ruin_step: the step index where ruin first occurred, or None
        ruin_shortfall: how far below ruin_threshold the ruin-stores sum was
            at ruin_step (pre-cap), or None if no ruin occurred
        ledger: per-step (Effect, Store) deltas, populated only if
            `record_ledger` is True (see Docs/01-Kern-Domaenenmodell.md,
            "Ledger") - instrumenting every Monte-Carlo run would be far more
            expensive than the aggregate result needs.
        computed_effect_final_states: post-run `parameters` state of every
            ComputedEffect, populated only if `record_ledger` is True
    """
    sim_stores = {store.name: copy.deepcopy(store) for store in plan.stores}
    time_series: list[dict[str, float]] = []
    ledger: list[LedgerEntry] = []
    ruin_step: int | None = None
    ruin_shortfall: float | None = None
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
            store_balances_before = {name: store.balance for name, store in sim_stores.items()}
            fixed_additions, total_growth_rates = _calculate_phase1_updates(
                plan.effects,
                t,
                active_phase,
                drawn_rates,
                store_names,
                store_balances_before,
                ledger if record_ledger else None,
            )

            # Apply Phase 1 updates to simulated stores
            for name, store in sim_stores.items():
                if total_growth_rates[name] != 0.0:
                    store.apply_percentage_growth(total_growth_rates[name])
                if fixed_additions[name] != 0.0:
                    store.add_amount(fixed_additions[name], t)

            # Phase 2: Computed effects (registered python functions)
            _execute_computed_effects(
                plan.effects, sim_stores, t, active_phase, plan, ledger if record_ledger else None
            )

            # Check for ruin (against pre-cap balances), then cap balances at 0
            ruin_step, ruin_shortfall = _cap_and_check_ruin(
                sim_stores, plan, t, ruin_step, ruin_shortfall
            )

            time_series.append({name: store.balance for name, store in sim_stores.items()})

        computed_effect_final_states = (
            _collect_computed_effect_final_states(plan.effects) if record_ledger else []
        )
    finally:
        plan.stores = original_stores
        plan.effects = original_effects

    final_balances = {name: store.balance for name, store in sim_stores.items()}
    return (
        final_balances,
        time_series,
        ruin_step,
        ruin_shortfall,
        ledger,
        computed_effect_final_states,
    )


def run_simulation(plan: Plan, record_ledger: bool = False) -> SimulationResult:
    """Run a single deterministic simulation run.

    `record_ledger=True` additionally instruments the run with a per-step
    ledger and computed-effect final states (see Docs/01, "Ledger").
    """
    final_balances, time_series, ruin_step, ruin_shortfall, ledger, states = (
        _run_single_simulation(plan, None, record_ledger)
    )
    return SimulationResult(
        final_balances=final_balances,
        time_series=time_series,
        ruin_step=ruin_step,
        ruin_shortfall=ruin_shortfall,
        ledger=ledger,
        computed_effect_final_states=states,
    )


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
    """Find the run index whose summed final balance (over `store_names`) is
    closest to the given percentile of that sum's distribution across runs.

    Used to pick a representative Monte-Carlo path (e.g. the median or the
    10th-percentile run) for later instrumented re-simulation (see
    Docs/01-Kern-Domaenenmodell.md, "Ledger").
    """
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
    """Re-run one specific Monte-Carlo run index with full ledger instrumentation.

    Reproduces exactly the same correlated-return draws `run_monte_carlo`
    used for the same (plan, num_runs, seed): the RNG is re-seeded
    identically and group draws are re-derived deterministically (see
    Docs/01-Kern-Domaenenmodell.md, "Korrelation") - only the requested
    `run_idx` is actually simulated, not all `num_runs`.
    """
    rng = np.random.default_rng(seed)
    all_groups = {**_default_correlation_groups(plan), **plan.correlation_groups}
    group_draws = _pre_draw_correlated_returns(plan, all_groups, num_runs, rng)
    run_drawn_rates = _drawn_rates_for_run(all_groups, group_draws, run_idx)

    final_balances, time_series, ruin_step, ruin_shortfall, ledger, states = (
        _run_single_simulation(plan, run_drawn_rates, record_ledger=True)
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
    """Run a Monte-Carlo simulation, then re-simulate a few representative
    paths - one per requested percentile, plus the deterministic reference
    run - with full per-step ledger instrumentation.

    Only these few runs are re-simulated with instrumentation, not every
    Monte-Carlo run, since keeping a ledger for every run would be far more
    expensive than the aggregate result needs (see
    Docs/01-Kern-Domaenenmodell.md, "Ledger"). `store_names` defaults to the
    plan's `ruin_stores`, falling back to every store if that's empty too.
    """
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
