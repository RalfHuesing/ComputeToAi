"""Tests for compare_plans() function in compare.py."""

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_monte_carlo
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline
from compute_to_ai.features.finance.cashflow import add_expense, add_income_stream
from compute_to_ai.features.finance.compare import compare_plans
from compute_to_ai.features.finance.portfolio import add_asset_class


def _make_simple_plan(name: str, income: float = 2000.0, expense: float = 1000.0) -> Plan:
    """Build a minimal plan with income, expense, and two phases."""
    plan = Plan(
        name=name,
        timeline=Timeline(step_count=5),
        stores=[Store(name="cash", balance=10000.0)],
        phases=[
            Phase(name="Erwerbsphase", start_step=0, end_step=3),
            Phase(name="Rentenphase", start_step=3, end_step=5),
        ],
        ruin_stores=["cash"],
        ruin_threshold=0.0,
    )
    add_income_stream(plan, "Gehalt", "cash", amount=income, active_phases=["Erwerbsphase"])
    add_income_stream(plan, "Rente", "cash", amount=800.0, active_phases=["Rentenphase"])
    add_expense(plan, "Lebenshaltung", "cash", amount=expense, inflation_rate=0.02)
    return plan


def test_compare_identical_plans_no_changes() -> None:
    """Two plans with identical configuration should show empty deltas."""
    plan_a = _make_simple_plan("plan-a")
    plan_b = _make_simple_plan("plan-a-copy")
    result = compare_plans(plan_a, None, plan_b, None)

    assert result["config_delta"]["stores"]["added"] == []
    assert result["config_delta"]["stores"]["removed"] == []
    assert result["config_delta"]["stores"]["modified"] == []
    assert result["config_delta"]["effects"]["added"] == []
    assert result["config_delta"]["effects"]["removed"] == []
    assert result["config_delta"]["effects"]["modified"] == []
    assert result["config_delta"]["phases"]["added"] == []
    assert result["config_delta"]["phases"]["removed"] == []
    assert result["config_delta"]["phases"]["modified"] == []


def test_compare_detects_added_store() -> None:
    plan_a = _make_simple_plan("a")
    plan_b = _make_simple_plan("b")
    plan_b.stores.append(Store(name="depot", balance=50000.0, description="ETF Depot"))

    result = compare_plans(plan_a, None, plan_b, None)

    added = result["config_delta"]["stores"]["added"]
    assert len(added) == 1
    assert added[0]["name"] == "depot"
    assert added[0]["balance"] == 50000.0
    assert added[0]["description"] == "ETF Depot"


def test_compare_detects_removed_store() -> None:
    plan_a = _make_simple_plan("a")
    plan_a.stores.append(Store(name="old_depot", balance=100.0))
    plan_b = _make_simple_plan("b")

    result = compare_plans(plan_a, None, plan_b, None)

    removed = result["config_delta"]["stores"]["removed"]
    assert len(removed) == 1
    assert removed[0]["name"] == "old_depot"


def test_compare_detects_modified_store_balance() -> None:
    plan_a = _make_simple_plan("a")
    plan_b = _make_simple_plan("b")
    plan_b.stores[0].balance = 20000.0  # change from 10000 to 20000

    result = compare_plans(plan_a, None, plan_b, None)

    modified = result["config_delta"]["stores"]["modified"]
    assert len(modified) == 1
    assert modified[0]["name"] == "cash"
    assert modified[0]["changes"]["balance"]["from"] == 10000.0
    assert modified[0]["changes"]["balance"]["to"] == 20000.0


def test_compare_detects_added_effect() -> None:
    plan_a = _make_simple_plan("a")
    plan_b = _make_simple_plan("b")
    plan_b.stores.append(Store(name="depot", balance=0.0))
    add_asset_class(
        plan_b, store_name="depot", initial_balance=0.0, expected_return=0.07, volatility=0.15
    )

    result = compare_plans(plan_a, None, plan_b, None)

    added_effects = result["config_delta"]["effects"]["added"]
    effect_keys = [e["key"] for e in added_effects]
    # add_asset_class creates a CorrelatedReturnEffect with name "Rendite {store_name}"
    assert "Rendite depot" in effect_keys


def test_compare_detects_modified_income_amount() -> None:
    plan_a = _make_simple_plan("a", income=2000.0)
    plan_b = _make_simple_plan("b", income=3000.0)  # higher income

    result = compare_plans(plan_a, None, plan_b, None)

    modified_effects = result["config_delta"]["effects"]["modified"]
    gehalt_change = next((e for e in modified_effects if e["key"] == "Gehalt"), None)
    assert gehalt_change is not None
    assert "amount_per_step" in gehalt_change["changes"]
    assert gehalt_change["changes"]["amount_per_step"]["from"] == 2000.0
    assert gehalt_change["changes"]["amount_per_step"]["to"] == 3000.0


def test_compare_detects_modified_phase() -> None:
    plan_a = _make_simple_plan("a")
    plan_b = _make_simple_plan("b")
    # Move retirement 1 year earlier
    plan_b.phases[0].end_step = 2
    plan_b.phases[1].start_step = 2

    result = compare_plans(plan_a, None, plan_b, None)

    modified_phases = result["config_delta"]["phases"]["modified"]
    assert len(modified_phases) >= 1


def test_compare_warns_on_timeline_mismatch() -> None:
    plan_a = _make_simple_plan("a")
    plan_b = Plan(
        name="b",
        timeline=Timeline(step_count=10),  # 10 vs 5 steps
        stores=[Store(name="cash", balance=10000.0)],
        ruin_stores=["cash"],
    )
    add_income_stream(plan_b, "Gehalt", "cash", amount=2000.0)

    result = compare_plans(plan_a, None, plan_b, None)

    assert len(result["warnings"]) > 0
    assert any("mismatch" in w for w in result["warnings"])


def test_compare_warns_on_missing_simulation_results() -> None:
    plan_a = _make_simple_plan("a")
    plan_b = _make_simple_plan("b")

    result = compare_plans(plan_a, None, plan_b, None)

    assert result["simulation_delta"] is None
    assert any("Monte Carlo" in w for w in result["warnings"])


def test_compare_simulation_delta_with_results() -> None:
    """Plans with simulations should show ruin_probability and percentile deltas."""
    # plan_a: income barely covers expenses - high ruin risk over 20 steps
    plan_a = Plan(
        name="stressed-a",
        timeline=Timeline(step_count=20),
        stores=[Store(name="cash", balance=100.0)],  # very low cushion
        ruin_stores=["cash"],
        ruin_threshold=0.0,
    )
    add_income_stream(plan_a, "Gehalt", "cash", amount=100.0)
    add_expense(
        plan_a, "Lebenshaltung", "cash", amount=500.0, inflation_rate=0.02
    )  # expenses >> income

    # plan_b: income far exceeds expenses - nearly zero ruin risk
    plan_b = Plan(
        name="healthy-b",
        timeline=Timeline(step_count=20),
        stores=[Store(name="cash", balance=100.0)],
        ruin_stores=["cash"],
        ruin_threshold=0.0,
    )
    add_income_stream(plan_b, "Gehalt", "cash", amount=2000.0)
    add_expense(plan_b, "Lebenshaltung", "cash", amount=500.0, inflation_rate=0.02)

    mc_a = run_monte_carlo(plan_a, num_runs=200, seed=42)
    mc_b = run_monte_carlo(plan_b, num_runs=200, seed=42)

    result = compare_plans(plan_a, mc_a, plan_b, mc_b)

    assert result["simulation_delta"] is not None
    assert "ruin_probability" in result["simulation_delta"]
    # Plan A (negative cashflow) should have higher ruin probability than plan B
    assert mc_a.ruin_probability > 0.0, "plan_a should have some ruins"
    diff = result["simulation_delta"]["ruin_probability"]["diff"]
    assert diff < 0, f"Expected plan_b to have lower ruin probability, diff={diff}"


def test_compare_description_field_in_stores_effects_and_phases() -> None:
    """Descriptions on stores, effects, and phases should be reflected in the config delta."""
    plan_a = _make_simple_plan("a")
    plan_a.stores[0].description = "Girokonto DKB"
    plan_a.phases[0].description = "Phase A"

    plan_b = _make_simple_plan("b")
    plan_b.stores[0].description = "Girokonto Sparkasse"  # changed store description
    plan_b.phases[0].description = "Phase B"  # changed phase description

    result = compare_plans(plan_a, None, plan_b, None)

    # 1. Store description check
    modified_stores = result["config_delta"]["stores"]["modified"]
    cash_change = next((m for m in modified_stores if m["name"] == "cash"), None)
    assert cash_change is not None
    assert "description" in cash_change["changes"]
    assert cash_change["changes"]["description"]["from"] == "Girokonto DKB"
    assert cash_change["changes"]["description"]["to"] == "Girokonto Sparkasse"

    # 2. Phase description check
    modified_phases = result["config_delta"]["phases"]["modified"]
    phase_change = next((p for p in modified_phases if p["name"] == "Erwerbsphase"), None)
    assert phase_change is not None
    assert "description" in phase_change["changes"]
    assert phase_change["changes"]["description"]["from"] == "Phase A"
    assert phase_change["changes"]["description"]["to"] == "Phase B"
