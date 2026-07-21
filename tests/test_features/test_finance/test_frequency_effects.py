"""Tests for frequency and interval-based cashflows in the finance domain.

See Docs/04-Feature-Finanzen-Methodik.md and tasks/task-4.11-frequenz-und-intervall-ausgaben/.
"""

import pytest

from compute_to_ai.engine.plan import Plan, Store, Timeline
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.features.finance.cashflow import (
    add_expense,
    add_income_stream,
    parse_frequency_to_interval,
)


def test_parse_frequency_to_interval() -> None:
    """Test frequency string conversion to step counts."""
    assert parse_frequency_to_interval("monthly") == 1
    assert parse_frequency_to_interval("quarterly") == 3
    assert parse_frequency_to_interval("yearly") == 12
    assert parse_frequency_to_interval("annual") == 12
    assert parse_frequency_to_interval("every_n_years", interval_years=5) == 60

    with pytest.raises(ValueError, match="interval_years must be at least 1"):
        parse_frequency_to_interval("every_n_years", interval_years=0)

    with pytest.raises(ValueError, match="Unknown frequency"):
        parse_frequency_to_interval("invalid_freq")


def test_yearly_expense_simulation() -> None:
    """Yearly expense of 1200 reduces cash store balance only at steps 0, 12, 24..."""
    plan = Plan(
        name="yearly_expense_plan",
        timeline=Timeline(step_count=25),
        stores=[Store(name="cash", balance=10000.0)],
    )
    add_expense(plan, name="KFZ-Versicherung", store_name="cash", amount=1200.0, frequency="yearly")

    result = run_simulation(plan)
    series = result.time_series

    # Step 0: 10000 - 1200 = 8800
    assert series[0]["cash"] == 8800.0
    # Steps 1..11: balance remains 8800
    for step in range(1, 12):
        assert series[step]["cash"] == 8800.0
    # Step 12: 8800 - 1200 = 7600
    assert series[12]["cash"] == 7600.0
    # Steps 13..23: balance remains 7600
    for step in range(13, 24):
        assert series[step]["cash"] == 7600.0
    # Step 24: 7600 - 1200 = 6400
    assert series[24]["cash"] == 6400.0


def test_every_n_years_expense_with_inflation() -> None:
    """Every 5 years expense with inflation compounds growth based on step index (1 + r)^t."""
    plan = Plan(
        name="turnus_plan",
        timeline=Timeline(step_count=61),
        stores=[Store(name="cash", balance=50000.0)],
    )
    add_expense(
        plan,
        name="Auto-Neuanschaffung",
        store_name="cash",
        amount=10000.0,
        inflation_rate=0.01,  # 1% per step
        frequency="every_n_years",
        interval_years=5,
    )

    result = run_simulation(plan)
    series = result.time_series

    # Step 0: 50000 - 10000 * (1.01^0) = 40000
    assert series[0]["cash"] == 40000.0
    # Step 59: balance remains 40000
    assert series[59]["cash"] == 40000.0
    # Step 60: 40000 - 10000 * (1.01^60)
    expected_step_60_deduction = 10000.0 * (1.01**60)
    assert pytest.approx(series[60]["cash"], rel=1e-5) == 40000.0 - expected_step_60_deduction


def test_offset_first_occurrence_income() -> None:
    """Quarterly income starting at step 3 (first_occurrence_step=3)."""
    plan = Plan(
        name="offset_income_plan",
        timeline=Timeline(step_count=10),
        stores=[Store(name="cash", balance=0.0)],
    )
    add_income_stream(
        plan,
        name="Bonus",
        store_name="cash",
        amount=500.0,
        frequency="quarterly",
        first_occurrence_step=3,
    )

    result = run_simulation(plan)
    series = result.time_series

    # Steps 0..2: balance 0
    for s in range(3):
        assert series[s]["cash"] == 0.0
    # Step 3: +500
    assert series[3]["cash"] == 500.0
    # Steps 4..5: 500
    assert series[4]["cash"] == 500.0
    assert series[5]["cash"] == 500.0
    # Step 6: +500 -> 1000
    assert series[6]["cash"] == 1000.0
    # Step 9: +500 -> 1500
    assert series[9]["cash"] == 1500.0
