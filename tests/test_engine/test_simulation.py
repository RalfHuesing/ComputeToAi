from typing import Any

import numpy as np
import pytest

from compute_to_ai.engine.effect import (
    ComputedEffect,
    CorrelatedReturnEffect,
    GrowingFixedEffect,
    PercentageGrowthEffect,
    TransferEffect,
    register_computed_effect,
)
from compute_to_ai.engine.plan import CorrelationGroup, Plan
from compute_to_ai.engine.simulation import (
    find_closest_run_to_percentile,
    run_monte_carlo,
    run_monte_carlo_path,
    run_path_audit,
    run_simulation,
)
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline


def test_growing_fixed_effect_compounds_growth() -> None:
    # Starting with 0, adding 100 per step growing at 10%
    # Step 0: 100 * 1.1^0 is 100
    # Step 1: 100 * 1.1^1 is 110
    # End balances should be 210
    plan = Plan(
        name="growing-fixed",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0)],
        effects=[GrowingFixedEffect(store_name="cash", amount_per_step=100.0, growth_rate=0.1)],
    )

    result = run_simulation(plan)
    assert result.final_balances["cash"] == 210.0
    assert result.time_series == [{"cash": 100.0}, {"cash": 210.0}]


def test_transfer_effect_conserves_and_splits_by_weight() -> None:
    # Step 0: transfer 100 * 1.1^0 = 100 from cash, split 60/40.
    # Step 1: transfer 100 * 1.1^1 = 110 from cash, split 60/40.
    plan = Plan(
        name="transfer-test",
        timeline=Timeline(step_count=2),
        stores=[
            Store(name="cash", balance=1000.0),
            Store(name="etf_a", balance=0.0),
            Store(name="etf_b", balance=0.0),
        ],
        effects=[
            TransferEffect(
                from_store_name="cash",
                to_store_weights={"etf_a": 0.6, "etf_b": 0.4},
                amount_per_step=100.0,
                growth_rate=0.10,
            )
        ],
    )

    result = run_simulation(plan)

    assert pytest.approx(result.final_balances["cash"]) == 790.0
    assert pytest.approx(result.final_balances["etf_a"]) == 126.0
    assert pytest.approx(result.final_balances["etf_b"]) == 84.0
    # Conservation: what cash lost, the destinations gained in aggregate.
    assert pytest.approx(1000.0 - result.final_balances["cash"]) == (
        result.final_balances["etf_a"] + result.final_balances["etf_b"]
    )


def test_percentage_growth_effect_compounds() -> None:
    # Starting with 100, growing by 5% per step
    # Step 0: 100 * 1.05 is 105
    # Step 1: 105 * 1.05 is 110.25
    plan = Plan(
        name="percentage-growth",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=100.0)],
        effects=[PercentageGrowthEffect(store_names=["cash"], growth_rate=0.05)],
    )

    result = run_simulation(plan)
    assert result.final_balances["cash"] == 110.25


def test_percentage_growth_effect_applies_same_rate_to_multiple_stores() -> None:
    # Two stores, one effect at 5% growth targeting both.
    # Step 0: 100 * 1.05 is 105 for each store
    # Step 1: 105 * 1.05 is 110.25 for each store
    plan = Plan(
        name="percentage-growth-multi-store",
        timeline=Timeline(step_count=2),
        stores=[Store(name="etf_a", balance=100.0), Store(name="etf_b", balance=100.0)],
        effects=[PercentageGrowthEffect(store_names=["etf_a", "etf_b"], growth_rate=0.05)],
    )

    result = run_simulation(plan)
    assert result.final_balances["etf_a"] == 110.25
    assert result.final_balances["etf_b"] == 110.25


def test_store_fifo_lot_consumption() -> None:
    store = Store(name="depot", balance=0.0)

    # Add three lots:
    # Lot 1: 10 units at step 0 (cost basis 50)
    # Lot 2: 20 units at step 1 (cost basis 120)
    store.add_amount(10.0, step=0, cost_basis=50.0, track_lots=True)
    store.add_amount(20.0, step=1, cost_basis=120.0, track_lots=True)

    assert store.balance == 30.0
    assert len(store.lots) == 2

    # Withdraw 15 units:
    # Consumes full Lot 1 (10 units) and partial Lot 2 (5 units)
    consumed = store.withdraw_amount(15.0)

    assert len(consumed) == 2
    assert consumed[0].quantity == 10.0
    assert consumed[0].created_step == 0
    assert consumed[1].quantity == 5.0
    assert consumed[1].created_step == 1

    assert store.balance == 15.0
    assert len(store.lots) == 1
    assert store.lots[0].quantity == 15.0
    assert store.lots[0].created_step == 1


def test_store_percentage_growth_applies_to_lots() -> None:
    store = Store(name="depot", balance=0.0)
    store.add_amount(10.0, step=0, cost_basis=50.0, track_lots=True)
    store.add_amount(20.0, step=1, cost_basis=120.0, track_lots=True)

    # Grow by 10%
    store.apply_percentage_growth(0.10)

    assert store.balance == 33.0
    assert store.lots[0].quantity == 11.0
    assert store.lots[0].cost_basis == 50.0  # cost basis does not grow
    assert store.lots[1].quantity == 22.0
    assert store.lots[1].cost_basis == 120.0


def test_effects_limited_by_phases() -> None:
    # Define phases: PhaseA [0, 1), PhaseB [1, 3)
    # Effect 1: GrowingFixed +10, only active in PhaseA
    # Effect 2: GrowingFixed +20, only active in PhaseB
    # Step 0: PhaseA is active. Effect 1 applies (+10) -> cash: 10
    # Step 1: PhaseB is active. Effect 2 applies (+20) -> cash: 30
    # Step 2: PhaseB is active. Effect 2 applies (+20) -> cash: 50
    plan = Plan(
        name="phase-limited",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=0.0)],
        phases=[
            Phase(name="PhaseA", start_step=0, end_step=1),
            Phase(name="PhaseB", start_step=1, end_step=3),
        ],
        effects=[
            GrowingFixedEffect(store_name="cash", amount_per_step=10.0, active_phases=["PhaseA"]),
            GrowingFixedEffect(store_name="cash", amount_per_step=20.0, active_phases=["PhaseB"]),
        ],
    )

    result = run_simulation(plan)
    assert result.final_balances["cash"] == 50.0
    assert result.time_series == [{"cash": 10.0}, {"cash": 30.0}, {"cash": 50.0}]


# Define a test computed effect
@register_computed_effect("test_tax")
def _test_tax_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], _step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    # Deduct tax from depot and add to tax_account
    rate = float(parameters.get("rate", 0.0))
    taxable = balances.get("depot", 0.0) * rate
    balances["depot"] -= taxable
    balances["tax_account"] = balances.get("tax_account", 0.0) + taxable


# Records execution order: each run appends its "digit" to "log" as the next
# least-significant decimal digit, so the final value's digit sequence (most
# significant first) is exactly the effects' execution order.
@register_computed_effect("order_marker")
def _order_marker_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], _step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    digit = int(parameters["digit"])
    balances["log"] = balances.get("log", 0.0) * 10 + digit


def test_computed_effect_runs_in_phase2() -> None:
    # Depot grows by 10% in Phase 1.
    # Then computed tax of 20% runs in Phase 2.
    # Start: depot is 100, tax_account is 0
    # Phase 1: depot is 110
    # Phase 2: tax is 22, depot is 88, tax_account is 22
    plan = Plan(
        name="computed-effect-test",
        timeline=Timeline(step_count=1),
        stores=[
            Store(name="depot", balance=100.0),
            Store(name="tax_account", balance=0.0),
        ],
        effects=[
            PercentageGrowthEffect(store_names=["depot"], growth_rate=0.10),
            ComputedEffect(function_name="test_tax", parameters={"rate": 0.20}),
        ],
    )

    result = run_simulation(plan)
    assert pytest.approx(result.final_balances["depot"]) == 88.0
    assert pytest.approx(result.final_balances["tax_account"]) == 22.0


def test_computed_effects_execute_in_order_regardless_of_append_order() -> None:
    plan = Plan(
        name="computed-effect-order-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="log", balance=0.0)],
        effects=[
            # Appended out of order - execution must follow `order`, not this.
            ComputedEffect(function_name="order_marker", parameters={"digit": 2}, order=10),
            ComputedEffect(function_name="order_marker", parameters={"digit": 1}, order=-10),
        ],
    )

    result = run_simulation(plan)
    assert result.final_balances["log"] == 12.0


def test_computed_effects_with_equal_order_keep_append_order() -> None:
    plan = Plan(
        name="computed-effect-tie-order-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="log", balance=0.0)],
        effects=[
            ComputedEffect(function_name="order_marker", parameters={"digit": 1}),
            ComputedEffect(function_name="order_marker", parameters={"digit": 2}),
        ],
    )

    result = run_simulation(plan)
    assert result.final_balances["log"] == 12.0


def test_ruin_checking() -> None:
    # Starts with 50, deducts 20 per step.
    # Step 0: 50 - 20 is 30
    # Step 1: 30 - 20 is 10
    # Step 2: 10 - 20 is -10 which caps at 0.0. Ruin triggers (balance below 5.0 threshold)
    plan = Plan(
        name="ruin-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=50.0)],
        effects=[GrowingFixedEffect(store_name="cash", amount_per_step=-20.0)],
        ruin_stores=["cash"],
        ruin_threshold=5.0,
    )

    result = run_simulation(plan)
    assert result.final_balances["cash"] == 0.0
    assert result.ruin_step == 2
    assert pytest.approx(result.ruin_shortfall) == 15.0


def test_ruin_checking_fires_at_default_zero_threshold() -> None:
    # Regression test: with the default ruin_threshold=0.0, a post-cap balance
    # is never negative, so ruin used to be undetectable. The check must run
    # against the pre-cap balance instead.
    plan = Plan(
        name="ruin-zero-threshold-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=50.0)],
        effects=[GrowingFixedEffect(store_name="cash", amount_per_step=-20.0)],
        ruin_stores=["cash"],
    )

    result = run_simulation(plan)
    assert result.final_balances["cash"] == 0.0
    assert result.ruin_step == 2
    assert pytest.approx(result.ruin_shortfall) == 10.0


def test_ruin_checking_reports_no_shortfall_when_no_ruin_occurs() -> None:
    plan = Plan(
        name="no-ruin-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=50.0)],
        effects=[GrowingFixedEffect(store_name="cash", amount_per_step=10.0)],
        ruin_stores=["cash"],
    )

    result = run_simulation(plan)
    assert result.ruin_step is None
    assert result.ruin_shortfall is None


def test_monte_carlo_ruin_shortfall_percentiles_populated_only_on_ruin() -> None:
    # No stochastic effects: every run is identical and ruins the same way.
    plan = Plan(
        name="mc-ruin-shortfall-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=50.0)],
        effects=[GrowingFixedEffect(store_name="cash", amount_per_step=-20.0)],
        ruin_stores=["cash"],
    )

    result = run_monte_carlo(plan, num_runs=5, seed=1)
    assert result.ruin_probability == 1.0
    assert result.ruin_shortfall_percentiles == {10: 10.0, 50: 10.0, 90: 10.0}


def test_monte_carlo_ruin_shortfall_percentiles_empty_without_ruin() -> None:
    plan = Plan(
        name="mc-no-ruin-shortfall-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=50.0)],
        effects=[GrowingFixedEffect(store_name="cash", amount_per_step=10.0)],
        ruin_stores=["cash"],
    )

    result = run_monte_carlo(plan, num_runs=5, seed=1)
    assert result.ruin_probability == 0.0
    assert result.ruin_shortfall_percentiles == {}


def test_correlated_returns_monte_carlo() -> None:
    # 2 assets: stocks and bonds
    # stocks return is 7%, vol is 15%
    # bonds return is 3%, vol is 5%
    # correlation is -0.5
    matrix = [[1.0, -0.5], [-0.5, 1.0]]
    plan = Plan(
        name="portfolio-stochastics",
        timeline=Timeline(step_count=10),
        stores=[
            Store(name="stocks", balance=100.0),
            Store(name="bonds", balance=100.0),
        ],
        effects=[
            CorrelatedReturnEffect(
                store_names=["stocks"],
                correlation_group="assets",
                expected_return=0.07,
                volatility=0.15,
            ),
            CorrelatedReturnEffect(
                store_names=["bonds"],
                correlation_group="assets",
                expected_return=0.03,
                volatility=0.05,
            ),
        ],
        correlation_groups={
            "assets": CorrelationGroup(matrix=matrix, store_names=["stocks", "bonds"])
        },
    )

    # Run deterministic first
    det_res = run_simulation(plan)
    # Stocks final is 196.715 (100 * 1.07^10)
    # Bonds final is 134.391 (100 * 1.03^10)
    assert pytest.approx(det_res.final_balances["stocks"], 1e-3) == 196.715
    assert pytest.approx(det_res.final_balances["bonds"], 1e-3) == 134.391

    # Run Monte Carlo
    mc_res = run_monte_carlo(plan, num_runs=500, seed=42)

    assert mc_res.num_runs == 500
    assert "stocks" in mc_res.final_balances_percentiles
    assert "bonds" in mc_res.final_balances_percentiles

    # Stocks median should be close to expected compounding
    p50_stocks = mc_res.final_balances_percentiles["stocks"][50]
    p50_bonds = mc_res.final_balances_percentiles["bonds"][50]

    # Verify that the drawn values are reasonable
    assert 100.0 < p50_stocks < 300.0
    assert 100.0 < p50_bonds < 200.0


def test_correlated_return_broadcasts_draw_to_stores_and_keeps_group_correlation() -> None:
    # Two ETF positions ("etf_a", "etf_b") tracking the same index share one
    # CorrelatedReturnEffect and must receive the identical drawn rate every
    # run/step. A third, single-store "bonds" effect in the same correlation
    # group must still be correlated with that shared draw as configured -
    # the regression risk when broadcasting one group draw to several stores.
    matrix = [[1.0, -0.9], [-0.9, 1.0]]
    plan = Plan(
        name="correlated-multi-store",
        timeline=Timeline(step_count=1),
        stores=[
            Store(name="etf_a", balance=100.0),
            Store(name="etf_b", balance=250.0),
            Store(name="bonds", balance=100.0),
        ],
        effects=[
            CorrelatedReturnEffect(
                store_names=["etf_a", "etf_b"],
                correlation_group="assets",
                expected_return=0.07,
                volatility=0.15,
            ),
            CorrelatedReturnEffect(
                store_names=["bonds"],
                correlation_group="assets",
                expected_return=0.03,
                volatility=0.05,
            ),
        ],
        correlation_groups={
            "assets": CorrelationGroup(matrix=matrix, store_names=["etf_a", "bonds"])
        },
    )

    num_runs = 2000
    mc_result = run_monte_carlo(plan, num_runs=num_runs, seed=11)

    # Same drawn rate every run: etf_a and etf_b start from different
    # balances, so the implied rate (delta / balance_before) - not the raw
    # delta - must be compared to prove it's literally the same float.
    for run_idx in (0, 1, num_runs - 1):
        path = run_monte_carlo_path(plan, run_idx, num_runs=num_runs, seed=11)
        deltas = {
            e.store_name: e.delta for e in path.ledger if e.effect_type == "correlated_return"
        }
        rate_a = deltas["etf_a"] / 100.0
        rate_b = deltas["etf_b"] / 250.0
        assert pytest.approx(rate_a, abs=1e-12) == rate_b

    # Correlation with the single-store "bonds" effect in the same group is
    # preserved: with step_count=1, final balance is a linear function of
    # the drawn rate, so the sample correlation of final balances mirrors
    # the configured -0.9 rate correlation.
    etf_a_finals = np.array([b["etf_a"] for b in mc_result.raw_final_balances])
    bonds_finals = np.array([b["bonds"] for b in mc_result.raw_final_balances])
    sample_corr = np.corrcoef(etf_a_finals, bonds_finals)[0, 1]
    assert sample_corr < -0.7


def test_ledger_records_growing_fixed_deltas() -> None:
    # 100/step growing at 10%: step 0 delta is 100, step 1 delta is 110.
    plan = Plan(
        name="ledger-growing-fixed",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0)],
        effects=[
            GrowingFixedEffect(
                name="Gehalt", store_name="cash", amount_per_step=100.0, growth_rate=0.1
            )
        ],
    )

    result = run_simulation(plan, record_ledger=True)

    assert [(e.step, e.effect_name, e.effect_type, e.store_name) for e in result.ledger] == [
        (0, "Gehalt", "growing_fixed", "cash"),
        (1, "Gehalt", "growing_fixed", "cash"),
    ]
    assert pytest.approx([e.delta for e in result.ledger]) == [100.0, 110.0]
    assert result.computed_effect_final_states == []


def test_ledger_records_transfer_deltas_split_by_weight() -> None:
    plan = Plan(
        name="ledger-transfer",
        timeline=Timeline(step_count=1),
        stores=[
            Store(name="cash", balance=1000.0),
            Store(name="etf_a", balance=0.0),
            Store(name="etf_b", balance=0.0),
        ],
        effects=[
            TransferEffect(
                name="Sparrate",
                from_store_name="cash",
                to_store_weights={"etf_a": 0.6, "etf_b": 0.4},
                amount_per_step=100.0,
            )
        ],
    )

    result = run_simulation(plan, record_ledger=True)

    entries = {(e.store_name, e.delta) for e in result.ledger}
    assert entries == {("cash", -100.0), ("etf_a", 60.0), ("etf_b", 40.0)}
    assert all(e.effect_type == "transfer" and e.effect_name == "Sparrate" for e in result.ledger)


def test_ledger_records_percentage_growth_delta_on_pre_step_balance() -> None:
    # 100 growing at 5%: delta is 100 * 0.05 = 5.0 (not the post-growth balance).
    plan = Plan(
        name="ledger-percentage-growth",
        timeline=Timeline(step_count=2),
        stores=[Store(name="depot", balance=100.0)],
        effects=[PercentageGrowthEffect(name="Rendite", store_names=["depot"], growth_rate=0.05)],
    )

    result = run_simulation(plan, record_ledger=True)

    assert pytest.approx(result.ledger[0].delta) == 5.0
    # Step 1 starts from 105.0 -> delta is 105.0 * 0.05 = 5.25.
    assert pytest.approx(result.ledger[1].delta) == 5.25


def test_ledger_skips_zero_delta_entries() -> None:
    # An active effect that computes to exactly 0 (0% interest) shouldn't
    # clutter the ledger with a no-op entry.
    plan = Plan(
        name="ledger-zero-delta",
        timeline=Timeline(step_count=1),
        stores=[Store(name="loan", balance=100.0)],
        effects=[PercentageGrowthEffect(store_names=["loan"], growth_rate=0.0)],
    )

    result = run_simulation(plan, record_ledger=True)

    assert result.ledger == []


def test_ledger_records_computed_effect_deltas_via_before_after_diff() -> None:
    # Depot grows by 10% in Phase 1 (delta 10.0), then a computed 20% tax
    # moves 22.0 from depot to tax_account in Phase 2.
    plan = Plan(
        name="ledger-computed-effect",
        timeline=Timeline(step_count=1),
        stores=[
            Store(name="depot", balance=100.0),
            Store(name="tax_account", balance=0.0),
        ],
        effects=[
            PercentageGrowthEffect(store_names=["depot"], growth_rate=0.10),
            ComputedEffect(name="Steuer", function_name="test_tax", parameters={"rate": 0.20}),
        ],
    )

    result = run_simulation(plan, record_ledger=True)

    computed_entries = {
        (e.store_name, round(e.delta, 6)) for e in result.ledger if e.effect_type == "computed"
    }
    assert computed_entries == {("depot", -22.0), ("tax_account", 22.0)}
    assert all(e.function_name == "test_tax" for e in result.ledger if e.effect_type == "computed")


@register_computed_effect("trigger_once")
def _trigger_once_func(  # pyright: ignore[reportUnusedFunction]
    _balances: dict[str, float], step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    """A minimal ComputedEffect exercising run-scoped `parameters` state,
    analogous to `flexible_acquisition`'s one-time `triggered_step` flag."""
    if parameters.get("triggered_step") is None and step >= int(parameters["trigger_at"]):
        parameters["triggered_step"] = step


def test_computed_effect_final_states_surfaces_run_scoped_parameters() -> None:
    plan = Plan(
        name="computed-effect-final-state",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=0.0)],
        effects=[
            ComputedEffect(
                name="Trigger", function_name="trigger_once", parameters={"trigger_at": 1}
            )
        ],
    )

    result = run_simulation(plan, record_ledger=True)

    assert len(result.computed_effect_final_states) == 1
    state = result.computed_effect_final_states[0]
    assert state.effect_name == "Trigger"
    assert state.function_name == "trigger_once"
    assert state.parameters["triggered_step"] == 1

    # Without instrumentation, this run-scoped state is discarded.
    plain_result = run_simulation(plan, record_ledger=False)
    assert plain_result.computed_effect_final_states == []


def test_find_closest_run_to_percentile_picks_nearest_sum() -> None:
    raw_final_balances = [{"cash": v} for v in [10.0, 20.0, 30.0, 40.0, 50.0]]

    median_idx = find_closest_run_to_percentile(raw_final_balances, ["cash"], 50)
    assert raw_final_balances[median_idx]["cash"] == 30.0

    low_idx = find_closest_run_to_percentile(raw_final_balances, ["cash"], 10)
    assert raw_final_balances[low_idx]["cash"] == 10.0


def test_run_monte_carlo_path_reproduces_the_original_run_exactly() -> None:
    matrix = [[1.0, -0.5], [-0.5, 1.0]]
    plan = Plan(
        name="path-reproduction",
        timeline=Timeline(step_count=5),
        stores=[Store(name="stocks", balance=100.0), Store(name="bonds", balance=100.0)],
        effects=[
            CorrelatedReturnEffect(
                store_names=["stocks"],
                correlation_group="assets",
                expected_return=0.07,
                volatility=0.15,
            ),
            CorrelatedReturnEffect(
                store_names=["bonds"],
                correlation_group="assets",
                expected_return=0.03,
                volatility=0.05,
            ),
        ],
        correlation_groups={
            "assets": CorrelationGroup(matrix=matrix, store_names=["stocks", "bonds"])
        },
    )

    mc_result = run_monte_carlo(plan, num_runs=20, seed=7)

    for run_idx in (0, 5, 19):
        reproduced = run_monte_carlo_path(plan, run_idx, num_runs=20, seed=7)
        assert reproduced.final_balances == pytest.approx(mc_result.raw_final_balances[run_idx])
        # Re-running with instrumentation must not change the underlying draws.
        assert reproduced.ledger  # correlated_return deltas were recorded


def test_run_path_audit_produces_instrumented_percentile_and_deterministic_paths() -> None:
    plan = Plan(
        name="path-audit-test",
        timeline=Timeline(step_count=5),
        stores=[Store(name="cash", balance=1000.0)],
        effects=[
            CorrelatedReturnEffect(
                store_names=["cash"],
                correlation_group="assets",
                expected_return=0.05,
                volatility=0.10,
            ),
            GrowingFixedEffect(name="Ausgabe", store_name="cash", amount_per_step=-50.0),
        ],
        ruin_stores=["cash"],
    )

    audit = run_path_audit(plan, num_runs=30, seed=3, percentiles=(50, 10))

    assert set(audit.paths) == {"p50", "p10", "deterministic"}
    assert audit.num_runs == 30
    for path in audit.paths.values():
        assert path.ledger  # every path is instrumented
        assert len(path.time_series) == 5

    # The deterministic path matches a plain deterministic run's final balance.
    det_reference = run_simulation(plan)
    assert audit.paths["deterministic"].final_balances == pytest.approx(
        det_reference.final_balances
    )


def test_simulation_is_thread_safe() -> None:
    import concurrent.futures

    plan = Plan(
        name="thread-safe-test",
        timeline=Timeline(step_count=10),
        stores=[Store(name="cash", balance=100.0)],
        effects=[GrowingFixedEffect(store_name="cash", amount_per_step=10.0)],
    )

    def run_one(_: int) -> float:
        result = run_simulation(plan)
        return result.final_balances["cash"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(run_one, range(20)))

    # All runs must produce the correct results (100 + 10 * 10 = 200)
    for res in results:
        assert res == 200.0
