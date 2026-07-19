import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline
from compute_to_ai.features.finance.cashflow import (
    add_expense,
    add_fixed_acquisition,
    add_flexible_acquisition,
    add_income_stream,
)
from compute_to_ai.features.finance.liability import add_liability
from compute_to_ai.features.finance.path_audit import (
    audit_plan,
    build_event_log,
    compute_category_series,
)
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


def test_audit_plan_flags_overlapping_income_on_same_store() -> None:
    plan = Plan(
        name="overlap-income-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0)],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=3000.0, start_step=0, end_step=0)
    add_income_stream(plan, "Rente", "cash", amount=2000.0, start_step=0, end_step=1)

    result = run_simulation(plan, record_ledger=True)
    findings = audit_plan(plan, result)

    overlap = [f for f in findings if "Gehalt" in f.message and "Rente" in f.message]
    assert len(overlap) == 1
    assert overlap[0].step == 0


def test_audit_plan_flags_income_less_phase() -> None:
    plan = Plan(
        name="income-less-phase-test",
        timeline=Timeline(step_count=4),
        stores=[Store(name="cash", balance=1000.0)],
        phases=[
            Phase(name="Erwerbsphase", start_step=0, end_step=2),
            Phase(name="Rentenphase", start_step=2, end_step=4),
        ],
        ruin_stores=["cash"],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=1000.0, active_phases=["Erwerbsphase"])

    result = run_simulation(plan, record_ledger=True)
    findings = audit_plan(plan, result)

    income_less = [f for f in findings if "Rentenphase" in f.message]
    assert len(income_less) == 1
    assert income_less[0].step == 2


def test_audit_plan_flags_growth_inflation_mismatch() -> None:
    plan = Plan(
        name="growth-mismatch-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=3)],
    )
    add_income_stream(
        plan, "Gehalt", "cash", amount=1000.0, growth_rate=0.02, active_phases=["Erwerbsphase"]
    )
    add_expense(
        plan, "Miete", "cash", amount=500.0, inflation_rate=0.0, active_phases=["Erwerbsphase"]
    )

    result = run_simulation(plan, record_ledger=True)
    findings = audit_plan(plan, result)

    mismatch = [f for f in findings if "grows" in f.message]
    assert len(mismatch) == 1


def test_audit_plan_flags_orphaned_store() -> None:
    plan = Plan(
        name="orphaned-store-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0), Store(name="forgotten", balance=500.0)],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=1000.0)

    result = run_simulation(plan, record_ledger=True)
    findings = audit_plan(plan, result)

    orphaned = [f for f in findings if "forgotten" in f.message]
    assert len(orphaned) == 1
    assert orphaned[0].step is None


def test_audit_plan_flags_unpaid_liability() -> None:
    plan = Plan(
        name="unpaid-liability-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=10000.0)],
    )
    add_liability(
        plan,
        name="Kredit",
        liability_store_name="kredit",
        cash_store_name="cash",
        principal=10000.0,
        interest_rate=0.05,
        payment=100.0,  # far too small to amortize within 2 steps
    )

    result = run_simulation(plan, record_ledger=True)
    findings = audit_plan(plan, result)

    unpaid = [f for f in findings if "kredit" in f.message]
    assert len(unpaid) == 1


def test_audit_plan_reports_no_findings_on_a_clean_plan() -> None:
    plan = Plan(
        name="clean-plan-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=3)],
        ruin_stores=["cash"],
    )
    add_income_stream(
        plan, "Gehalt", "cash", amount=2000.0, growth_rate=0.02, active_phases=["Erwerbsphase"]
    )
    add_expense(
        plan, "Miete", "cash", amount=500.0, inflation_rate=0.02, active_phases=["Erwerbsphase"]
    )

    result = run_simulation(plan, record_ledger=True)
    findings = audit_plan(plan, result)

    assert findings == []


# ---------------------------------------------------------------------------
# Tests for compute_category_series with real-money inflation adjustment
# ---------------------------------------------------------------------------


def test_compute_category_series_annual_real_deflates_future_values() -> None:
    """With annual_real granularity, step t values are divided by (1 + rate)^t.

    Step 0 is unaffected (divisor = 1). Steps 1+ are deflated.
    We use a 100% inflation_rate to make the divisor powers obvious:
    - step 0: income 1000 / 2^0 = 1000
    - step 1: income 1000 / 2^1 = 500
    """
    plan = Plan(
        name="real-money-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0)],
    )
    # Constant income with inflation_rate=1.0 (100%) so the plan's internal
    # rate is picked up by _find_plan_inflation_rate through the expense effect.
    add_income_stream(plan, "Gehalt", "cash", amount=1000.0)
    add_expense(
        plan, "Lebenshaltung", "cash", amount=0.0, inflation_rate=1.0
    )  # sets plan inflation rate

    result = run_simulation(plan, record_ledger=True)
    series = compute_category_series(plan, result, granularity="annual_real")

    assert len(series) == 2
    # Step 0: no deflation
    assert pytest.approx(series[0].income, abs=1e-6) == 1000.0
    # Step 1: deflated by (1+1.0)^1 = 2
    assert pytest.approx(series[1].income, abs=1e-6) == 500.0


def test_compute_category_series_monthly_average_real_combines_divisors() -> None:
    """monthly_average_real should deflate AND divide by 12."""
    plan = Plan(
        name="real-monthly-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0)],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=1200.0)
    add_expense(plan, "Lebenshaltung", "cash", amount=0.0, inflation_rate=1.0)  # 100% inflation

    result = run_simulation(plan, record_ledger=True)
    series = compute_category_series(plan, result, granularity="monthly_average_real")

    # Step 0: 1200 / 12 = 100 (no inflation at step 0)
    assert pytest.approx(series[0].income, abs=1e-6) == 100.0
    # Step 1: 1200 / (2^1 * 12) = 50
    assert pytest.approx(series[1].income, abs=1e-6) == 50.0


def test_compute_category_series_real_balances_are_also_deflated() -> None:
    """Balances in real granularity should be divided by the cumulative inflation factor."""
    plan = Plan(
        name="real-balances-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0)],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=1000.0)
    add_expense(plan, "Lebenshaltung", "cash", amount=0.0, inflation_rate=1.0)

    result = run_simulation(plan, record_ledger=True)
    nominal = compute_category_series(plan, result, granularity="annual")
    real = compute_category_series(plan, result, granularity="annual_real")

    # Step 0: real and nominal are the same (divisor = 1)
    assert real[0].balances["cash"] == pytest.approx(nominal[0].balances["cash"], abs=1e-6)
    # Step 1: real cash balance is half the nominal
    assert real[1].balances["cash"] == pytest.approx(nominal[1].balances["cash"] / 2.0, abs=1e-6)


def test_compute_category_series_annual_real_zero_inflation_unchanged() -> None:
    """With 0% inflation the 'real' series must equal the nominal series."""
    plan = Plan(
        name="zero-inflation-real-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=100.0)],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=500.0)
    add_expense(plan, "Lebenshaltung", "cash", amount=200.0, inflation_rate=0.0)

    result = run_simulation(plan, record_ledger=True)
    nominal = compute_category_series(plan, result, granularity="annual")
    real = compute_category_series(plan, result, granularity="annual_real")

    for n, r in zip(nominal, real, strict=True):
        assert pytest.approx(n.income) == r.income
        assert pytest.approx(n.expenses) == r.expenses
        for store in n.balances:
            assert pytest.approx(n.balances[store]) == r.balances[store]


# ---------------------------------------------------------------------------
# Tests for get_percentile_curves
# ---------------------------------------------------------------------------


def _build_audit_plan() -> Plan:
    """Build a plan with liquid, invested, and liability stores for curve tests."""
    plan = Plan(
        name="curves-test",
        timeline=Timeline(step_count=4),
        stores=[Store(name="cash", balance=1000.0)],
        ruin_stores=["cash"],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=500.0)
    add_expense(plan, "Lebenshaltung", "cash", amount=200.0, inflation_rate=0.02)
    add_asset_class(
        plan, store_name="depot", initial_balance=2000.0, expected_return=0.07, volatility=0.15
    )
    add_liability(
        plan,
        name="Kredit",
        liability_store_name="kredit",
        cash_store_name="cash",
        principal=3000.0,
        interest_rate=0.05,
        payment=500.0,
    )
    return plan


def test_get_percentile_curves_returns_correct_keys() -> None:
    from compute_to_ai.engine.simulation import run_path_audit
    from compute_to_ai.features.finance.path_audit import get_percentile_curves

    plan = _build_audit_plan()
    audit = run_path_audit(plan, num_runs=20, seed=42)

    curves = get_percentile_curves(plan, audit)

    # Must have one entry per path in the audit
    assert set(curves.keys()) == set(audit.paths.keys())


def test_get_percentile_curves_step_fields_present() -> None:
    from compute_to_ai.engine.simulation import run_path_audit
    from compute_to_ai.features.finance.path_audit import get_percentile_curves

    plan = _build_audit_plan()
    audit = run_path_audit(plan, num_runs=20, seed=42)
    curves = get_percentile_curves(plan, audit)

    for path_key, steps in curves.items():
        assert len(steps) == plan.timeline.step_count, (
            f"wrong number of steps for path {path_key!r}"
        )
        for step in steps:
            assert "step" in step
            assert "liquid" in step
            assert "invested" in step
            assert "liabilities" in step
            assert "total_net" in step


def test_get_percentile_curves_classifies_stores_correctly() -> None:
    """Depot should be invested, kredit should be liabilities, cash should be liquid."""
    from compute_to_ai.engine.simulation import run_path_audit
    from compute_to_ai.features.finance.path_audit import get_percentile_curves

    plan = _build_audit_plan()
    audit = run_path_audit(plan, num_runs=20, seed=42)
    curves = get_percentile_curves(plan, audit)

    # Use the deterministic path for reproducibility
    det_steps = curves["deterministic"]

    # Step 0: liquid is cash (1000 init + 500 income - 200 expense - 500 credit rate = approx 800)
    # invested is positive (depot), liabilities are positive (kredit)
    first = det_steps[0]
    assert first["invested"] > 0.0, "depot should contribute to invested"
    assert first["liabilities"] > 0.0, "kredit should contribute to liabilities"
    # total net calculation: liquid + invested - liabilities
    assert pytest.approx(first["total_net"]) == (
        first["liquid"] + first["invested"] - first["liabilities"]
    )


def test_get_percentile_curves_total_net_equals_sum() -> None:
    """total_net must always equal liquid + invested - liabilities for every step/path."""
    from compute_to_ai.engine.simulation import run_path_audit
    from compute_to_ai.features.finance.path_audit import get_percentile_curves

    plan = _build_audit_plan()
    audit = run_path_audit(plan, num_runs=20, seed=42)
    curves = get_percentile_curves(plan, audit)

    for path_key, steps in curves.items():
        for step in steps:
            expected = step["liquid"] + step["invested"] - step["liabilities"]
            assert pytest.approx(step["total_net"], abs=1e-6) == expected, (
                f"total_net mismatch at step {step['step']} for path {path_key!r}"
            )


def test_get_percentile_curves_liquid_only_plan() -> None:
    """A plan with only cash stores should have invested=0 and liabilities=0."""
    from compute_to_ai.engine.simulation import run_path_audit
    from compute_to_ai.features.finance.path_audit import get_percentile_curves

    plan = Plan(
        name="liquid-only-curves",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=500.0)],
        ruin_stores=["cash"],
    )
    add_income_stream(plan, "Gehalt", "cash", amount=300.0)
    audit = run_path_audit(plan, num_runs=10, seed=1)
    curves = get_percentile_curves(plan, audit)

    for path_key, steps in curves.items():
        for step in steps:
            assert step["invested"] == 0.0, (
                f"no asset classes, invested should be 0 (path {path_key!r})"
            )
            assert step["liabilities"] == 0.0, f"no liabilities (path {path_key!r})"
