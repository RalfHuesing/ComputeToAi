"""Tests for cash bucket de-risking glidepath before phase transitions and acquisitions."""

import pytest

from compute_to_ai.engine.plan import Phase, Plan, Timeline
from compute_to_ai.engine.store import Store
from compute_to_ai.features.finance.portfolio import (
    add_cash_bucket,
    cash_bucket_manager_func,
)


def test_cash_bucket_glidepath_linear_increase() -> None:
    """Test that cash bucket target size increases linearly over 36 steps before retirement."""
    timeline = Timeline(step_count=180)
    phases = [
        Phase(name="Erwerb", start_step=0, end_step=120),
        Phase(name="Ruhestand", start_step=120, end_step=180),
    ]
    plan = Plan(
        name="Glidepath Plan",
        timeline=timeline,
        phases=phases,
        stores=[Store(name="cash", balance=0.0), Store(name="stocks", balance=0.0)],
    )

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"stocks": 1.0},
        emergency_buffer_months={"Erwerb": 3.0, "Ruhestand": 6.0},
        monthly_expenses=2000.0,
        glidepath_steps=36,
    )

    # Initial balance at step 0
    balances = {"cash": 6000.0, "stocks": 100000.0}

    # Step 0 to 83: before ramp start (120 - 36 = 84)
    for step in range(84):
        cash_bucket_manager_func(balances, step, plan.effects[0].parameters, plan)
        assert balances["cash"] == 6000.0

    # Step 84: start of ramp (fraction 0.0) -> target = 6000
    cash_bucket_manager_func(balances, 84, plan.effects[0].parameters, plan)
    assert balances["cash"] == 6000.0

    # Step 102: halfway through ramp (fraction 18/36 = 0.5) -> target = 6000 + 0.5 * 6000 = 9000
    cash_bucket_manager_func(balances, 102, plan.effects[0].parameters, plan)
    assert balances["cash"] == 9000.0

    # Step 120: retirement phase starts -> target = 12000
    cash_bucket_manager_func(balances, 120, plan.effects[0].parameters, plan)
    assert balances["cash"] == 12000.0


def test_cash_bucket_glidepath_dynamic_shortening() -> None:
    """Test that if remaining steps before phase change are fewer than glidepath_steps,
    the ramp dynamically shortens to available steps.
    """
    timeline = Timeline(step_count=60)
    phases = [
        Phase(name="Erwerb", start_step=0, end_step=24),
        Phase(name="Ruhestand", start_step=24, end_step=60),
    ]
    plan = Plan(
        name="Short Ramp Plan",
        timeline=timeline,
        phases=phases,
        stores=[Store(name="cash", balance=0.0), Store(name="stocks", balance=0.0)],
    )

    # Requested 36 steps, but only 24 steps exist in Erwerbsphase
    add_cash_bucket(
        plan=plan,
        portfolio_weights={"stocks": 1.0},
        emergency_buffer_months={"Erwerb": 3.0, "Ruhestand": 6.0},
        monthly_expenses=2000.0,
        glidepath_steps=36,
    )

    balances = {"cash": 6000.0, "stocks": 100000.0}

    # Step 0: start of shortened ramp -> target = 6000
    cash_bucket_manager_func(balances, 0, plan.effects[0].parameters, plan)
    assert balances["cash"] == 6000.0

    # Step 12: halfway through available 24 steps -> fraction 0.5 -> target = 9000
    cash_bucket_manager_func(balances, 12, plan.effects[0].parameters, plan)
    assert balances["cash"] == 9000.0

    # Step 24: retirement starts -> target = 12000
    cash_bucket_manager_func(balances, 24, plan.effects[0].parameters, plan)
    assert balances["cash"] == 12000.0


def test_sequence_of_returns_glidepath_protection() -> None:
    """Golden Test: Proves that linear glidepath de-risking protects portfolio wealth
    against Sequence-of-Returns risk (market crash right at retirement entry).
    """
    timeline = Timeline(step_count=150)
    phases = [
        Phase(name="Erwerb", start_step=0, end_step=120),
        Phase(name="Ruhestand", start_step=120, end_step=150),
    ]

    # Scenario A: Abrupt (no glidepath)
    plan_abrupt = Plan(
        name="Abrupt",
        timeline=timeline,
        phases=phases,
        stores=[Store(name="cash", balance=0.0), Store(name="stocks", balance=0.0)],
    )
    add_cash_bucket(
        plan=plan_abrupt,
        portfolio_weights={"stocks": 1.0},
        emergency_buffer_months={"Erwerb": 3.0, "Ruhestand": 24.0},
        monthly_expenses=2000.0,
        glidepath_steps=0,
    )
    bal_abrupt = {"cash": 6000.0, "stocks": 100000.0}

    # Simulate up to step 119
    for s in range(120):
        cash_bucket_manager_func(bal_abrupt, s, plan_abrupt.effects[0].parameters, plan_abrupt)

    # Market crash at step 120: stocks lose 50%
    bal_abrupt["stocks"] *= 0.50  # 100,000 -> 50,000

    # Step 120: abrupt target jump from 6000 to 48000 forces selling at crashed prices
    cash_bucket_manager_func(bal_abrupt, 120, plan_abrupt.effects[0].parameters, plan_abrupt)
    total_abrupt = bal_abrupt["cash"] + bal_abrupt["stocks"]

    # Scenario B: Glidepath (36 steps de-risking)
    plan_glidepath = Plan(
        name="Glidepath",
        timeline=timeline,
        phases=phases,
        stores=[Store(name="cash", balance=0.0), Store(name="stocks", balance=0.0)],
    )
    add_cash_bucket(
        plan=plan_glidepath,
        portfolio_weights={"stocks": 1.0},
        emergency_buffer_months={"Erwerb": 3.0, "Ruhestand": 24.0},
        monthly_expenses=2000.0,
        glidepath_steps=36,
    )
    bal_glidepath = {"cash": 6000.0, "stocks": 100000.0}

    # Simulate up to step 119 (linear de-risking builds cash to 48000 before crash)
    for s in range(120):
        cash_bucket_manager_func(
            bal_glidepath, s, plan_glidepath.effects[0].parameters, plan_glidepath
        )

    # Market crash at step 120: stocks lose 50%
    bal_glidepath["stocks"] *= 0.50  # 58,000 -> 29,000

    # Step 120: target is already 48000, no forced selling at crashed prices!
    cash_bucket_manager_func(
        bal_glidepath, 120, plan_glidepath.effects[0].parameters, plan_glidepath
    )
    total_glidepath = bal_glidepath["cash"] + bal_glidepath["stocks"]

    # Verify that glidepath significantly preserves wealth (+20,416.67 € preserved from crash)
    assert pytest.approx(total_abrupt) == 56000.0
    assert pytest.approx(total_glidepath, 1e-2) == 76416.67
    assert total_glidepath > total_abrupt
