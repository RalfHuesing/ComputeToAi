import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_monte_carlo, run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline
from compute_to_ai.features.finance.portfolio import (
    add_asset_class,
    add_cash_bucket,
    add_portfolio_rebalancing,
    set_correlation_matrix,
)


def test_portfolio_rebalancing_deterministic() -> None:
    plan = Plan(
        name="rebalance-deterministic",
        timeline=Timeline(step_count=2),
        stores=[],
    )

    # Add asset classes using the helper
    add_asset_class(
        plan=plan,
        store_name="equity",
        initial_balance=70.0,
        expected_return=0.20,
        volatility=0.15,
    )
    add_asset_class(
        plan=plan,
        store_name="bond",
        initial_balance=30.0,
        expected_return=0.10,
        volatility=0.05,
    )

    # Add rebalancing computed effect
    add_portfolio_rebalancing(
        plan=plan,
        name="Portfolio Rebalancing",
        weights={"equity": 0.70, "bond": 0.30},
    )

    result = run_simulation(plan)

    # Step 0:
    # Phase 1: equity grows by 20% to 84.0. bond grows by 10% to 33.0.
    # Total portfolio = 84 + 33 = 117.
    # Phase 2: rebalanced to 70/30.
    # equity target: 117 * 0.70 = 81.9
    # bond target: 117 * 0.30 = 35.1
    assert pytest.approx(result.time_series[0]["equity"]) == 81.9
    assert pytest.approx(result.time_series[0]["bond"]) == 35.1

    # Step 1:
    # Phase 1:
    # equity grows by 20%: 81.9 * 1.2 = 98.28.
    # bond grows by 10%: 35.1 * 1.1 = 38.61.
    # Total portfolio = 98.28 + 38.61 = 136.89.
    # Phase 2: rebalanced to 70/30.
    # equity target: 136.89 * 0.70 = 95.823
    # bond target: 136.89 * 0.30 = 41.067
    assert pytest.approx(result.final_balances["equity"]) == 95.823
    assert pytest.approx(result.final_balances["bond"]) == 41.067


def test_portfolio_rebalancing_stochastic() -> None:
    plan = Plan(
        name="rebalance-stochastic",
        timeline=Timeline(step_count=3),
        stores=[],
    )

    add_asset_class(
        plan=plan,
        store_name="equity",
        initial_balance=70.0,
        expected_return=0.07,
        volatility=0.15,
    )
    add_asset_class(
        plan=plan,
        store_name="bond",
        initial_balance=30.0,
        expected_return=0.03,
        volatility=0.05,
    )

    # Set correlation matrix
    set_correlation_matrix(
        plan=plan,
        group_name="portfolio",
        matrix=[[1.0, -0.2], [-0.2, 1.0]],
        store_names=["equity", "bond"],
    )

    # Add rebalancing computed effect
    add_portfolio_rebalancing(
        plan=plan,
        name="Rebalancing",
        weights={"equity": 0.70, "bond": 0.30},
    )

    # Run Monte Carlo
    mc_result = run_monte_carlo(plan, num_runs=5, seed=42)

    # In every run, the final proportion of equity / bond must be exactly 70 / 30
    for final_bal in mc_result.raw_final_balances:
        eq_final = final_bal["equity"]
        bd_final = final_bal["bond"]
        total = eq_final + bd_final
        assert pytest.approx(eq_final / total) == 0.70
        assert pytest.approx(bd_final / total) == 0.30


def test_cash_bucket_excess_moves_to_portfolio() -> None:
    from compute_to_ai.engine.timeline import Phase
    plan = Plan(
        name="cash-bucket-excess-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=100.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(plan, "equity", 0.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 0.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Erwerbsphase": 3.0},
        monthly_expenses=10.0,
    )

    result = run_simulation(plan)

    # Target Cash is 3.0 * 10 = 30. Excess is 70.
    # Equity gets 49, Bond gets 21. Cash stays at 30.
    assert pytest.approx(result.final_balances["cash"]) == 30.0
    assert pytest.approx(result.final_balances["equity"]) == 49.0
    assert pytest.approx(result.final_balances["bond"]) == 21.0


def test_cash_bucket_deficit_pulls_from_portfolio() -> None:
    from compute_to_ai.engine.timeline import Phase
    plan = Plan(
        name="cash-bucket-deficit-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(plan, "equity", 70.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 30.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Erwerbsphase": 3.0},
        monthly_expenses=10.0,
    )

    result = run_simulation(plan)

    # Target Cash is 30. Deficit is 30.
    # equity has 70.0 - 21.0 = 49.0
    # bond has 30.0 - 9.0 = 21.0
    assert pytest.approx(result.final_balances["cash"]) == 30.0
    assert pytest.approx(result.final_balances["equity"]) == 49.0
    assert pytest.approx(result.final_balances["bond"]) == 21.0


def test_cash_bucket_with_near_horizon_expenses() -> None:
    from compute_to_ai.engine.timeline import Phase
    from compute_to_ai.features.finance.cashflow import add_fixed_acquisition
    plan = Plan(
        name="cash-bucket-near-horizon-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=100.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(plan, "equity", 0.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 0.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Erwerbsphase": 3.0},
        monthly_expenses=10.0,
        near_horizon_steps=2,
    )

    # Add a fixed acquisition at step 2 of amount 50
    add_fixed_acquisition(plan, "Car", "cash", amount=50.0, step=2)

    result = run_simulation(plan)

    # At step 0:
    # Buffer 1: 3 * 10 = 30
    # Buffer 2: fixed acquisition of 50 at step 2 falls in near-horizon (s=1,2).
    # Buffer 2 is 50.
    # Total Target Cash is 80. Excess is 20.
    # Equity gets 14, Bond gets 6. Cash stays at 80.
    assert pytest.approx(result.time_series[0]["cash"]) == 80.0
    assert pytest.approx(result.time_series[0]["equity"]) == 14.0
    assert pytest.approx(result.time_series[0]["bond"]) == 6.0

