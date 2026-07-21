import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline
from compute_to_ai.features.finance.cashflow import add_income_stream
from compute_to_ai.features.finance.pension import (
    add_statutory_pension,
    calculate_pension_adjustment_factor,
)
from compute_to_ai.features.finance.phases import build_standard_life_phases


def test_adjustment_factor_is_one_with_no_early_or_late_months() -> None:
    factor = calculate_pension_adjustment_factor()
    assert factor == 1.0


def test_adjustment_factor_reduces_for_early_claiming() -> None:
    # 4 years early = 48 months * 0.3%/month = 14.4% reduction.
    factor = calculate_pension_adjustment_factor(months_early=48)
    assert pytest.approx(factor) == 0.856


def test_adjustment_factor_caps_the_early_reduction() -> None:
    # 5 years early would be 18% uncapped; the 14.4% cap applies instead.
    factor = calculate_pension_adjustment_factor(months_early=60)
    assert pytest.approx(factor) == 0.856


def test_adjustment_factor_increases_for_deferred_claiming() -> None:
    # 2 years late = 24 months * 0.5%/month = 12% bonus, uncapped.
    factor = calculate_pension_adjustment_factor(months_late=24)
    assert pytest.approx(factor) == 1.12


def test_adjustment_factor_rejects_both_early_and_late_months() -> None:
    with pytest.raises(ValueError, match="only one"):
        calculate_pension_adjustment_factor(months_early=12, months_late=12)


def test_add_statutory_pension_applies_adjustment_and_starts_on_time() -> None:
    plan = Plan(
        name="pension-test",
        timeline=Timeline(step_count=45),
        stores=[Store(name="cash", balance=0.0)],
    )

    add_statutory_pension(
        plan=plan,
        name="Rente",
        store_name="cash",
        annual_amount_at_regular_retirement_age=12000.0,
        regular_retirement_step=47,
        actual_retirement_step=43,
    )

    result = run_simulation(plan)

    # Not started yet: last simulated step is 44, still before start_step=43? No -
    # start_step=43 is within [0, 45), so the pension is active for steps 43-44.
    # Annual amount = 1000 * 12 * 0.856 = 10272.0, paid for 2 steps (43, 44).
    assert result.time_series[42]["cash"] == 0.0
    assert pytest.approx(result.final_balances["cash"]) == 10272.0 * 2


def test_add_statutory_pension_rejects_unknown_phase_name() -> None:
    plan = Plan(
        name="pension-unknown-phase-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Rentenphase", start_step=0, end_step=1)],
    )

    with pytest.raises(ValueError, match="retirement"):
        add_statutory_pension(
            plan=plan,
            name="Rente",
            store_name="cash",
            annual_amount_at_regular_retirement_age=12000.0,
            regular_retirement_step=0,
            actual_retirement_step=0,
            active_phases=["retirement"],
        )


def test_add_statutory_pension_rejects_unknown_store_name() -> None:
    plan = Plan(
        name="pension-unknown-store-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
    )

    with pytest.raises(ValueError, match="kasse"):
        add_statutory_pension(
            plan=plan,
            name="Rente",
            store_name="kasse",
            annual_amount_at_regular_retirement_age=12000.0,
            regular_retirement_step=0,
            actual_retirement_step=0,
        )
    assert plan.effects == []


def test_income_stream_to_pension_transition_across_early_retirement_gap() -> None:
    """Epic 3.7: Erwerbsende and gesetzlicher Rentenbeginn trigger the income source switch."""
    phases = build_standard_life_phases(
        current_age=60,
        employment_end_age=63,
        statutory_pension_start_age=67,
        life_expectancy_age=70,
    )
    plan = Plan(
        name="transition-test",
        timeline=Timeline(step_count=10),
        stores=[Store(name="cash", balance=0.0)],
        phases=phases,
    )

    add_income_stream(plan, "Gehalt", "cash", amount=3000.0, active_phases=["Erwerbsphase"])
    add_statutory_pension(
        plan=plan,
        name="Rente",
        store_name="cash",
        annual_amount_at_regular_retirement_age=18000.0,
        regular_retirement_step=7,
        actual_retirement_step=7,
        active_phases=["Rentenphase"],
    )

    result = run_simulation(plan)

    # Steps 0-2 (Erwerbsphase): salary of 3000/step.
    for step in range(3):
        assert result.time_series[step]["cash"] == pytest.approx(3000.0 * (step + 1))
    # Steps 3-6 (Frühruhestandslücke): no income at all, cash stays flat at 9000.
    for step in range(3, 7):
        assert result.time_series[step]["cash"] == pytest.approx(9000.0)
    # Steps 7-9 (Rentenphase): pension of 1500*12=18000/step.
    assert result.time_series[7]["cash"] == pytest.approx(9000.0 + 18000.0)
    assert result.final_balances["cash"] == pytest.approx(9000.0 + 18000.0 * 3)
