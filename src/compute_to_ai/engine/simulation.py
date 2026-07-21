"""SimulationRun execution - see Docs/01-Kern-Domaenenmodell.md.

A single deterministic pass or Monte-Carlo runs over the Timeline,
applying each Effect to its Store at every step.
"""

import copy

import numpy as np

from compute_to_ai.engine._simulation_phase1 import _calculate_phase1_updates, _ledger_entry
from compute_to_ai.engine.effect import ComputedEffect, CorrelatedReturnEffect, Effect
from compute_to_ai.engine.monte_carlo import (
    find_closest_run_to_percentile,
    run_monte_carlo,
    run_monte_carlo_path,
    run_path_audit,
)
from compute_to_ai.engine.plan import CorrelationGroup, Plan
from compute_to_ai.engine.result import (
    ComputedEffectFinalState,
    LedgerEntry,
    SimulationResult,
)
from compute_to_ai.engine.store import Store


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

    An effect covering multiple stores contributes only its representative
    axis identifier (`store_names[0]`) - all its stores share a single draw
    (see `CorrelatedReturnEffect`), so they need only one axis in the matrix.
    """
    referenced: dict[str, list[str]] = {}
    for effect in plan.effects:
        if not isinstance(effect, CorrelatedReturnEffect):
            continue
        group_name = effect.correlation_group
        if group_name in plan.correlation_groups:
            continue
        axis_name = effect.store_names[0]
        stores = referenced.setdefault(group_name, [])
        if axis_name not in stores:
            stores.append(axis_name)

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
            # `store_name` here is an axis identifier of the correlation
            # matrix, matched against each CorrelatedReturnEffect's
            # representative store (store_names[0]) - see
            # _default_correlation_groups.
            effect = None
            for eff in plan.effects:
                if (
                    isinstance(eff, CorrelatedReturnEffect)
                    and eff.store_names[0] == store_name
                    and eff.correlation_group == group_name
                ):
                    effect = eff
                    break

            if effect is not None:
                means[idx] = effect.expected_return
                vols[idx] = effect.volatility
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
    computed = [e for e in effects if isinstance(e, ComputedEffect)]
    for effect in sorted(computed, key=lambda e: e.order):
        if effect.is_active(t, active_phase):
            func_name = effect.function_name
            params = effect.parameters

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
        if not isinstance(effect, ComputedEffect):
            continue
        func_name = effect.function_name
        states.append(
            ComputedEffectFinalState(
                effect_name=effect.name if effect.name is not None else func_name,
                function_name=func_name,
                parameters=dict(effect.parameters),
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
    sim_plan = copy.deepcopy(plan)
    sim_stores = {store.name: store for store in sim_plan.stores}
    time_series: list[dict[str, float]] = []
    ledger: list[LedgerEntry] = []
    ruin_step: int | None = None
    ruin_shortfall: float | None = None
    store_names = list(sim_stores.keys())

    for t in range(sim_plan.timeline.step_count):
        active_phase = sim_plan.get_active_phase_name(t)
        for store in sim_stores.values():
            store.withdrawn_lots_this_step = []

        # Phase 1: Growth and fixed additive effects
        store_balances_before = {name: store.balance for name, store in sim_stores.items()}
        fixed_additions, total_growth_rates = _calculate_phase1_updates(
            sim_plan.effects,
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
            sim_plan.effects,
            sim_stores,
            t,
            active_phase,
            sim_plan,
            ledger if record_ledger else None,
        )

        # Check for ruin (against pre-cap balances), then cap balances at 0
        ruin_step, ruin_shortfall = _cap_and_check_ruin(
            sim_stores, sim_plan, t, ruin_step, ruin_shortfall
        )

        time_series.append({name: store.balance for name, store in sim_stores.items()})

    computed_effect_final_states = (
        _collect_computed_effect_final_states(sim_plan.effects) if record_ledger else []
    )

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
    final_balances, time_series, ruin_step, ruin_shortfall, ledger, states = _run_single_simulation(
        plan, None, record_ledger
    )
    return SimulationResult(
        final_balances=final_balances,
        time_series=time_series,
        ruin_step=ruin_step,
        ruin_shortfall=ruin_shortfall,
        ledger=ledger,
        computed_effect_final_states=states,
    )


__all__ = [
    "find_closest_run_to_percentile",
    "run_monte_carlo",
    "run_monte_carlo_path",
    "run_path_audit",
    "run_simulation",
]
