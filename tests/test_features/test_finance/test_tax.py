"""Unit tests for German tax features (withholding tax, Vorabpauschale, rent taxation).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

import pytest

from compute_to_ai.engine.effect import (
    ComputedEffect,
    GrowingFixedEffect,
    register_computed_effect,
)
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Lot, Store
from compute_to_ai.engine.timeline import Phase, Timeline
from compute_to_ai.features.finance.portfolio import add_asset_class, add_cash_bucket
from compute_to_ai.features.finance.tax import AssetClassTaxConfig, IncomeTaxTariff, add_tax_manager


@register_computed_effect("sell_all")
def sell_all_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float],
    _step: int,
    _parameters: dict[str, Any],
    _plan: Plan,
) -> None:
    """Computed effect that sells all equity."""
    balances["cash"] += balances["equity"]
    balances["equity"] = 0.0


@register_computed_effect("sell_all_step1")
def sell_all_step1_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float],
    step: int,
    _parameters: dict[str, Any],
    _plan: Plan,
) -> None:
    """Computed effect that sells all accumulating equity in step 1."""
    if step == 1:
        balances["cash"] += balances["equity_acc"]
        balances["equity_acc"] = 0.0


@register_computed_effect("sell_all_alt")
def sell_all_alt_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float],
    _step: int,
    _parameters: dict[str, Any],
    _plan: Plan,
) -> None:
    """Computed effect that sells all equity including pre-2009 lots."""
    balances["cash"] += balances["equity"]
    balances["equity"] = 0.0


def test_withholding_tax_and_allowance() -> None:
    plan = Plan(
        name="withholding-tax-test",
        timeline=Timeline(step_count=1),
        stores=[
            Store(name="cash", balance=100.0),
            Store(
                name="equity",
                balance=1500.0,
                lots=[Lot(quantity=1500.0, cost_basis=500.0, created_step=0)],
            ),
        ],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_tax_manager(
        plan=plan,
        cash_store_name="cash",
        sparerpauschbetrag=800.0,
        asset_classes={"equity": AssetClassTaxConfig(partial_exemption_rate=0.0)},
    )

    plan.effects.insert(0, ComputedEffect(name="Sell All", function_name="sell_all"))

    result = run_simulation(plan)

    # Gain: 1000. Under sparerpauschbetrag: 800.
    # Taxable: 200. Tax: 200 * 0.25 * 1.055 = 52.75.
    # Final cash: 100 (start) + 1500 (sale) - 52.75 (tax) = 1547.25
    assert pytest.approx(result.final_balances["cash"]) == 1547.25
    assert pytest.approx(result.final_balances["equity"]) == 0.0


def test_vorabpauschale_increases_basis() -> None:
    plan = Plan(
        name="vorabpauschale-test",
        timeline=Timeline(step_count=2),
        stores=[
            Store(name="cash", balance=100.0),
        ],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(
        plan=plan,
        store_name="equity_acc",
        initial_balance=1000.0,
        expected_return=0.10,
        volatility=0.0,
    )

    add_tax_manager(
        plan=plan,
        cash_store_name="cash",
        sparerpauschbetrag=0.0,
        basiszins=0.02,
        asset_classes={
            "equity_acc": AssetClassTaxConfig(
                partial_exemption_rate=0.0, is_accumulating=True, growth_rate=0.10
            )
        },
    )

    plan.effects.insert(
        0,
        ComputedEffect(name="Sell Step 1", function_name="sell_all_step1", start_step=1),
    )

    result = run_simulation(plan)

    # Trace:
    # Step 0:
    # Phase 1: equity_acc grows by 10% to 1100. (actual growth = 100)
    # Phase 2:
    #   q_start = 1000. potential_vorab = 1000 * 0.02 * 0.7 = 14.
    #   vorab = min(14, 100) = 14.
    #   Tax = 14 * 0.25 * 1.055 = 3.6925.
    #   Cash becomes 100 - 3.6925 = 96.3075.
    #   equity_acc lot's tracked vorabpauschale_taxed becomes 14.0.
    # Step 1:
    # Phase 1: equity_acc grows by 10% to 1210.
    # Phase 2:
    #   sell_all_step1 runs: cash becomes 96.3075 + 1210 = 1306.3075, equity_acc becomes 0.
    #   capital_gains_tax_manager runs:
    #     withdraw 1210. Raw gain = 1210 - 1000 = 210.
    #     taxable_gain = max(0, 210 - 14.0) = 196.0.
    #     Tax = 196.0 * 0.25 * 1.055 = 51.695.
    #     Cash becomes 1306.3075 - 51.695 = 1254.6125.
    assert pytest.approx(result.final_balances["cash"]) == 1254.6125
    assert pytest.approx(result.final_balances["equity_acc"]) == 0.0


def test_altfaelle_bestandsschutz() -> None:
    plan = Plan(
        name="altfaelle-test",
        timeline=Timeline(step_count=1),
        stores=[
            Store(name="cash", balance=100.0),
            Store(
                name="equity",
                balance=1000.0,
                lots=[Lot(quantity=1000.0, cost_basis=500.0, created_step=-5)],
            ),
        ],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_tax_manager(
        plan=plan,
        cash_store_name="cash",
        sparerpauschbetrag=0.0,
        asset_classes={"equity": AssetClassTaxConfig(partial_exemption_rate=0.0)},
    )

    plan.effects.insert(0, ComputedEffect(name="Sell All Alt", function_name="sell_all_alt"))

    result = run_simulation(plan)

    # Since created_step < 0, the gain of 500 is completely tax-free.
    # Cash becomes 100 + 1000 = 1100.
    assert pytest.approx(result.final_balances["cash"]) == 1100.0
    assert pytest.approx(result.final_balances["equity"]) == 0.0


def test_progressive_rent_taxation() -> None:
    """Test GKV/PV deductions and progressive income tax tariff on pension income.

    The phase is deliberately named "Ruhestand" rather than "Rentenphase" to prove
    that pension taxation is triggered solely by the explicit `retirement_step`
    parameter, never by matching the phase's (opaque) name.
    """
    plan = Plan(
        name="rent-tax-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Ruhestand", start_step=0, end_step=10)],
        effects=[GrowingFixedEffect(name="Rente", store_name="cash", amount_per_step=40000.0)],
    )

    add_tax_manager(
        plan=plan,
        cash_store_name="cash",
        tariff=IncomeTaxTariff(basic_allowance=12348.0),
        kvdr_rate=0.0875,
        pv_rate=0.042,
        retirement_step=0,
        start_year=2026,
    )

    result = run_simulation(plan)

    # Calculations (§ 32a EStG 2026, see Docs/09-Quellen.md):
    # Rent income = 40000.0
    # Taxable share = 84% (pension start 2026) -> 33600.0
    # Insurance = 40000 * (8.75% + 4.2%) = 40000 * 12.95% = 5180.0
    # ZV = max(0, 33600.0 - 12348.0 - 5180.0) = 16072.0
    # y = (16072.0 - 12348.0) / 10000 = 0.3724
    # Tax = (914.51 * 0.3724 + 1400.0) * 0.3724 = 648.18585634
    # Final cash = 40000.0 - 5180.0 - 648.18585634 = 34171.81414366
    assert pytest.approx(result.final_balances["cash"]) == 34171.81414366


def test_pension_tax_is_deducted_before_cash_bucket_sweeps_to_target() -> None:
    """Regression test: the pension income tax manager must run before the
    Cash-Bucket-Manager, or the bucket sweeps cash to its full target before
    tax is deducted, permanently landing short of the target by the tax
    amount every step."""
    plan = Plan(
        name="pension-tax-before-bucket-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
        effects=[GrowingFixedEffect(name="Rente", store_name="cash", amount_per_step=40000.0)],
    )

    add_tax_manager(
        plan=plan,
        cash_store_name="cash",
        tariff=IncomeTaxTariff(basic_allowance=12348.0),
        retirement_step=0,
        start_year=2026,
    )
    add_cash_bucket(
        plan=plan,
        portfolio_weights={},
        emergency_buffer_months={"": 12.0},
        monthly_expenses=1000.0,
        cash_store_name="cash",
    )

    result = run_simulation(plan)

    # Rent income 40000, insurance 5180.0, income tax 648.18585634 (same
    # calculation as test_progressive_rent_taxation) deducted first, then the
    # bucket manager sweeps cash to its target of 12 * 1000 = 12000 - not
    # 12000 minus the tax amount.
    assert pytest.approx(result.final_balances["cash"]) == 12000.0


def test_capital_gains_tax_fires_on_same_step_cash_bucket_sale() -> None:
    """Regression test: the capital gains tax manager must run after the
    Cash-Bucket-Manager, since it taxes `withdrawn_lots_this_step` - a
    withdrawal the bucket manager triggers in the same step."""
    plan = Plan(
        name="capital-gains-same-step-sale-test",
        timeline=Timeline(step_count=1),
        stores=[
            Store(name="cash", balance=0.0),
            Store(
                name="equity",
                balance=2000.0,
                lots=[Lot(quantity=2000.0, cost_basis=1000.0, created_step=0)],
            ),
        ],
    )

    add_tax_manager(
        plan=plan,
        cash_store_name="cash",
        sparerpauschbetrag=0.0,
        asset_classes={"equity": AssetClassTaxConfig(partial_exemption_rate=0.0)},
    )
    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 1.0},
        emergency_buffer_months={"": 12.0},
        monthly_expenses=100.0,
        cash_store_name="cash",
    )

    result = run_simulation(plan)

    # Bucket target = 12 * 100 = 1200; withdraws 1200 from equity (gain 600
    # of the 1200 withdrawn, cost basis 1000/2000 * 1200 = 600). Capital
    # gains tax = 600 * 0.25 * 1.055 = 158.25, deducted the same step.
    assert pytest.approx(result.final_balances["cash"]) == 1041.75
    assert pytest.approx(result.final_balances["equity"]) == 800.0
