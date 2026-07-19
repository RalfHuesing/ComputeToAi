import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline
from compute_to_ai.features.finance.cashflow import (
    add_fixed_acquisition,
    add_flexible_acquisition,
    add_income_stream,
)
from compute_to_ai.features.finance.liability import add_liability
from compute_to_ai.features.finance.path_audit import build_event_log, compute_category_series
from compute_to_ai.features.finance.portfolio import add_asset_class
from compute_to_ai.features.finance.tax import add_tax_manager


def _build_six_category_plan() -> Plan:
    """A one-step plan exercising all six categories at once.

    Hand-computed (see test docstrings below):
    - income: Gehalt (+1000)
    - expenses: Kredit Rate (-300, on cash)
    - taxes: pension income tax manager's insurance premium (-129.5, no
      income tax owed since 840 taxable rent stays below the basic allowance)
    - returns: equity's expected 5% return (+50, on a non-liability store)
    - reallocations: Kredit Zins (+50) and Kredit Tilgung (-300) on the
      liability store itself, net -250 - the "Rate" expense above already
      accounts for the real cash outflow of that payment
    """
    plan = Plan(
        name="six-category-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=1000.0)
    add_liability(
        plan,
        name="Kredit",
        liability_store_name="kredit",
        cash_store_name="cash",
        principal=1000.0,
        interest_rate=0.05,
        payment=300.0,
    )
    add_asset_class(
        plan, store_name="equity", initial_balance=1000.0, expected_return=0.05, volatility=0.10
    )
    add_tax_manager(plan, retirement_step=0)
    return plan


def test_compute_category_series_classifies_all_six_categories() -> None:
    plan = _build_six_category_plan()

    result = run_simulation(plan, record_ledger=True)
    series = compute_category_series(plan, result)

    assert len(series) == 1
    step = series[0]
    assert step.step == 0
    assert pytest.approx(step.income) == 1000.0
    assert pytest.approx(step.expenses) == 300.0
    assert pytest.approx(step.taxes) == 129.5
    assert pytest.approx(step.returns) == 50.0
    assert pytest.approx(step.reallocations) == -250.0
    assert step.balances["cash"] == pytest.approx(570.5)
    assert step.balances["kredit"] == pytest.approx(750.0)
    assert step.balances["equity"] == pytest.approx(1050.0)


def test_compute_category_series_monthly_average_divides_flows_not_balances() -> None:
    plan = _build_six_category_plan()
    result = run_simulation(plan, record_ledger=True)

    series = compute_category_series(plan, result, granularity="monthly_average")

    step = series[0]
    assert pytest.approx(step.income) == 1000.0 / 12.0
    assert pytest.approx(step.expenses) == 300.0 / 12.0
    assert pytest.approx(step.taxes) == 129.5 / 12.0
    # balances are a point-in-time snapshot, not a flow - never divided.
    assert step.balances["cash"] == pytest.approx(570.5)


def test_build_event_log_detects_phase_transition() -> None:
    plan = Plan(
        name="phase-transition-event-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=0.0)],
        phases=[
            Phase(name="A", start_step=0, end_step=1),
            Phase(name="B", start_step=1, end_step=3),
        ],
    )

    result = run_simulation(plan, record_ledger=True)
    events = build_event_log(plan, result)

    assert len(events) == 1
    assert events[0].step == 1
    assert events[0].event_type == "phase_transition"


def test_build_event_log_detects_liability_paid_off_in_the_first_step() -> None:
    # 0% interest, payment == principal: fully paid off already in step 0.
    plan = Plan(
        name="liability-payoff-event-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=1000.0)],
    )
    add_liability(
        plan,
        name="Kredit",
        liability_store_name="kredit",
        cash_store_name="cash",
        principal=300.0,
        interest_rate=0.0,
        payment=300.0,
    )

    result = run_simulation(plan, record_ledger=True)
    events = build_event_log(plan, result)

    paid_off = [e for e in events if e.event_type == "liability_paid_off"]
    assert len(paid_off) == 1
    assert paid_off[0].step == 0


def test_build_event_log_detects_fixed_acquisition_triggered() -> None:
    plan = Plan(
        name="fixed-acquisition-event-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=1000.0)],
    )
    add_fixed_acquisition(plan, "Auto", "cash", amount=500.0, step=1)

    result = run_simulation(plan, record_ledger=True)
    events = build_event_log(plan, result)

    assert len(events) == 1
    assert events[0].step == 1
    assert events[0].event_type == "acquisition_triggered"
    assert "Auto" in events[0].description


def test_build_event_log_ignores_a_windfall_single_step_income() -> None:
    # A Sondereinnahme (windfall) is structurally the same primitive
    # (start_step == end_step) but positive - not an acquisition.
    plan = Plan(
        name="windfall-event-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0)],
    )
    add_income_stream(plan, "Erbschaft", "cash", amount=5000.0, start_step=0, end_step=0)

    result = run_simulation(plan, record_ledger=True)
    events = build_event_log(plan, result)

    assert events == []


def test_build_event_log_detects_flexible_acquisition_triggered() -> None:
    plan = Plan(
        name="flexible-acquisition-event-test",
        timeline=Timeline(step_count=6),
        stores=[
            Store(name="risky", balance=2000.0),
            Store(name="safe", balance=0.0),
        ],
    )
    add_flexible_acquisition(
        plan,
        name="Urlaub",
        amount=1000.0,
        target_step=5,
        tolerance_steps=1,
        risky_store_name="risky",
        safe_store_name="safe",
        glidepath_start_step=0,
    )

    result = run_simulation(plan, record_ledger=True)
    events = build_event_log(plan, result)

    assert len(events) == 1
    assert events[0].event_type == "acquisition_triggered"
    assert "Urlaub" in events[0].description
    # Trigger fires once the reference-path check first passes, at step 4
    # (see Docs/04-Feature-Finanzen-Methodik.md, "Trigger-Logik").
    assert events[0].step == 4
