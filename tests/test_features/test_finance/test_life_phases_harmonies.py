"""Tests for life-phase and timeline harmonization (Task 4.12 Step 2)."""

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline
from compute_to_ai.features.finance.cashflow import add_income_stream
from compute_to_ai.features.finance.phases import build_standard_life_phases
from compute_to_ai.features.finance.portfolio import add_cash_bucket


def test_build_standard_life_phases_with_timeline_step_count() -> None:
    phases = build_standard_life_phases(
        current_age=30,
        employment_end_age=67,
        statutory_pension_start_age=67,
        life_expectancy_age=85,
        timeline_step_count=60,
    )
    # 85 - 30 = 55, but timeline_step_count is 60, so final pension phase end_step is 60
    assert phases[-1].name == "Rentenphase"
    assert phases[-1].end_step == 60


def test_cash_bucket_retains_emergency_buffer_at_timeline_end() -> None:
    # 5 steps plan (steps 0, 1, 2, 3, 4)
    # Phase A runs steps 0..3 (ends at step 3)
    # Phase B runs steps 3..4 (ends at step 4)
    # With end_step 4, step 4 is past end_step 4, but active_phase fallback keeps Phase B active
    plan = Plan(
        name="cash-bucket-harmony-test",
        timeline=Timeline(step_count=5),
        stores=[Store(name="cash", balance=1000.0)],
        phases=[
            Phase(name="Erwerbsphase", start_step=0, end_step=3),
            Phase(name="Rentenphase", start_step=3, end_step=4),
        ],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=500.0)
    add_cash_bucket(
        plan,
        cash_store_name="cash",
        portfolio_weights={},
        emergency_buffer_months={"Erwerbsphase": 3.0, "Rentenphase": 6.0},
        monthly_expenses=100.0,
    )

    result = run_simulation(plan)
    # Check that at step 4 (the last step), cash balance is maintained according to
    # Rentenphase buffer (6 * 100 = 600)
    assert result.time_series[-1]["cash"] >= 600.0
