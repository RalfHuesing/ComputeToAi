"""Tests for finance reports module: Asset Allocation, Sale Tax Estimator, Plan vs Actuals.

See Docs/04-Feature-Finanzen-Methodik.md and tasks/task-4.10-auswertungen-und-reports/.
"""

import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.store import Lot, Store
from compute_to_ai.engine.timeline import Timeline
from compute_to_ai.features.finance.portfolio import add_asset_class, add_portfolio_rebalancing
from compute_to_ai.features.finance.position import PositionMetadata, PositionRegistry
from compute_to_ai.features.finance.reports import (
    compare_plan_actuals,
    estimate_sale_tax,
    get_asset_allocation_report,
)


@pytest.fixture
def sample_plan() -> Plan:
    """Create a sample plan with 2 asset classes (Aktien 70%, Anleihen 30%) and cash."""
    plan = Plan(name="TestPlan", timeline=Timeline(step_count=10))

    add_asset_class(
        plan, "etf_world", initial_balance=7000.0, expected_return=0.07, volatility=0.15
    )
    add_asset_class(
        plan, "etf_bonds", initial_balance=3000.0, expected_return=0.03, volatility=0.05
    )
    plan.stores.append(Store(name="cash", balance=1000.0))

    add_portfolio_rebalancing(
        plan,
        name="Target Rebalancing",
        weights={"etf_world": 0.70, "etf_bonds": 0.30},
    )
    return plan


@pytest.fixture
def sample_registry() -> PositionRegistry:
    """Create a position registry with asset types."""
    return PositionRegistry(
        positions={
            "etf_world": PositionMetadata(
                isin_or_wkn="IE00B4L5Y983",
                shares=100.0,
                exchange="Xetra",
                last_updated="2026-07-21",
                asset_type="equity_fund",
            ),
            "etf_bonds": PositionMetadata(
                isin_or_wkn="IE00B1FZS350",
                shares=50.0,
                exchange="Xetra",
                last_updated="2026-07-21",
                asset_type="bond_fund",
            ),
        }
    )


# ============================================================================
# Step 1 Tests: get_asset_allocation_report
# ============================================================================


def test_get_asset_allocation_report_happy_path(
    sample_plan: Plan, sample_registry: PositionRegistry
) -> None:
    """Happy Path: 2 asset classes, exact total value, weights, drift, gains."""
    world_store = sample_plan.store("etf_world")
    world_store.lots = [
        Lot(quantity=7000.0, created_step=0, cost_basis=5000.0),
    ]

    report = get_asset_allocation_report(sample_plan, position_registry=sample_registry)

    assert report["total_portfolio_value"] == 10000.0
    assert len(report["asset_classes"]) == 2

    ac_world = next(
        ac for ac in report["asset_classes"] if ac["asset_class"] == "Rendite etf_world"
    )
    assert ac_world["actual_value"] == 7000.0
    assert ac_world["actual_weight"] == pytest.approx(0.70)
    assert ac_world["target_weight"] == 0.70
    assert ac_world["drift"] == pytest.approx(0.0)

    pos_world = ac_world["positions"][0]
    assert pos_world["store_name"] == "etf_world"
    assert pos_world["cost_basis"] == 5000.0
    assert pos_world["unrealized_gain"] == 2000.0
    assert pos_world["unrealized_gain_percent"] == pytest.approx(40.0)


def test_get_asset_allocation_report_zero_total_value() -> None:
    """Edge Case: Portfolio with 0 € total value returns 0.0 weights without ZeroDivisionError."""
    plan = Plan(name="ZeroPlan", timeline=Timeline(step_count=5))
    add_asset_class(plan, "etf_zero", initial_balance=0.0, expected_return=0.05, volatility=0.1)
    plan.store("etf_zero").lots = []
    plan.store("etf_zero").balance = 0.0

    add_portfolio_rebalancing(plan, name="Rebal", weights={"etf_zero": 1.0})

    report = get_asset_allocation_report(plan)
    assert report["total_portfolio_value"] == 0.0
    ac = report["asset_classes"][0]
    assert ac["actual_weight"] == 0.0
    assert ac["drift"] == -1.0


def test_get_asset_allocation_report_no_lots_fallback(sample_plan: Plan) -> None:
    """Edge Case: Store without lot history falls back to balance as cost basis."""
    sample_plan.store("etf_world").lots = []

    report = get_asset_allocation_report(sample_plan)
    pos = next(p for p in report["positions"] if p["store_name"] == "etf_world")
    assert pos["cost_basis"] == 7000.0
    assert pos["unrealized_gain"] == 0.0


def test_get_asset_allocation_report_pre_2009_lots(sample_plan: Plan) -> None:
    """Edge Case: Mixture of pre-2009 Bestandsschutz lots and regular lots."""
    store = sample_plan.store("etf_world")
    store.lots = [
        Lot(quantity=3000.0, created_step=0, cost_basis=1000.0, rule_version="pre_2009"),
        Lot(quantity=4000.0, created_step=0, cost_basis=3000.0),
    ]

    report = get_asset_allocation_report(sample_plan)
    pos = next(p for p in report["positions"] if p["store_name"] == "etf_world")

    assert pos["pre_2009_cost_basis"] == 1000.0
    assert pos["pre_2009_unrealized_gain"] == 2000.0
    assert pos["regular_cost_basis"] == 3000.0
    assert pos["regular_unrealized_gain"] == 1000.0
    assert pos["cost_basis"] == 4000.0
    assert pos["unrealized_gain"] == 3000.0


# ============================================================================
# Step 2 Tests: estimate_sale_tax
# ============================================================================


def test_estimate_sale_tax_happy_path(sample_plan: Plan, sample_registry: PositionRegistry) -> None:
    """Happy Path: Sale of equity fund with 2000€ gain, 30% exemption, 1000€ saver's allowance."""
    store = sample_plan.store("etf_world")
    store.balance = 7000.0
    store.lots = [Lot(quantity=7000.0, created_step=0, cost_basis=5000.0)]

    result = estimate_sale_tax(
        plan=sample_plan,
        store_name="etf_world",
        position_registry=sample_registry,
        sell_all=True,
        remaining_savers_allowance=1000.0,
    )

    assert result["gross_sale_amount"] == 7000.0
    assert result["gross_gain"] == 2000.0
    assert result["partial_exemption_rate"] == 0.30
    assert result["partial_exemption_amount"] == 600.0
    assert result["taxable_gain_after_exemption"] == 1400.0
    assert result["savers_allowance_used"] == 1000.0
    assert result["net_taxable_gain"] == 400.0
    assert result["abgeltungsteuer"] == 100.0
    assert result["soli"] == 5.50
    assert result["total_tax"] == 105.50
    assert result["net_proceeds"] == 7000.0 - 105.50


def test_estimate_sale_tax_excess_shares_error(
    sample_plan: Plan, sample_registry: PositionRegistry
) -> None:
    """Edge Case: Requesting to sell more shares than in metadata raises ValueError."""
    with pytest.raises(ValueError, match=r"Requested selling 150\.0 shares"):
        estimate_sale_tax(
            plan=sample_plan,
            store_name="etf_world",
            position_registry=sample_registry,
            shares_to_sell=150.0,
        )


def test_estimate_sale_tax_loss_sale(sample_plan: Plan, sample_registry: PositionRegistry) -> None:
    """Edge Case: Sale at a loss results in 0 € tax."""
    store = sample_plan.store("etf_world")
    store.balance = 4000.0
    store.lots = [Lot(quantity=4000.0, created_step=0, cost_basis=5000.0)]

    result = estimate_sale_tax(
        plan=sample_plan,
        store_name="etf_world",
        position_registry=sample_registry,
        sell_all=True,
    )

    assert result["gross_gain"] == -1000.0
    assert result["taxable_gain_before_exemption"] == 0.0
    assert result["total_tax"] == 0.0


def test_estimate_sale_tax_pre_2009_bestandsschutz(
    sample_plan: Plan, sample_registry: PositionRegistry
) -> None:
    """Edge Case: Sale of pre-2009 lots is tax exempt."""
    store = sample_plan.store("etf_world")
    store.balance = 7000.0
    store.lots = [Lot(quantity=7000.0, created_step=0, cost_basis=2000.0, rule_version="pre_2009")]

    result = estimate_sale_tax(
        plan=sample_plan,
        store_name="etf_world",
        position_registry=sample_registry,
        sell_all=True,
    )

    assert result["pre_2009_exempt_gain"] == 5000.0
    assert result["taxable_gain_before_exemption"] == 0.0
    assert result["total_tax"] == 0.0


# ============================================================================
# Step 3 Tests: compare_plan_actuals
# ============================================================================


def test_compare_plan_actuals_happy_path(sample_plan: Plan) -> None:
    """Happy Path: Plan actuals comparison runs and classifies net worth against percentiles."""
    result = compare_plan_actuals(sample_plan, current_step=0)

    assert result["current_step"] == 0
    assert result["current_net_worth"] == 11000.0
    assert result["status"] in (
        "BELOW_P10",
        "BETWEEN_P10_AND_P50",
        "BETWEEN_P50_AND_P90",
        "ABOVE_P90",
    )
    assert "p50_net_worth" in result
    assert "delta_to_p50_eur" in result


def test_compare_plan_actuals_step_out_of_bounds(sample_plan: Plan) -> None:
    """Edge Case: current_step out of horizon bounds raises ValueError."""
    with pytest.raises(ValueError, match="out of bounds"):
        compare_plan_actuals(sample_plan, current_step=999)
