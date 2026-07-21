"""Tests for cash bucket de-risking glidepath before phase transitions and acquisitions."""

from compute_to_ai.engine.plan import Phase, Plan, Timeline
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
    plan = Plan(name="Glidepath Plan", timeline=timeline, phases=phases)

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
    plan = Plan(name="Short Ramp Plan", timeline=timeline, phases=phases)

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
