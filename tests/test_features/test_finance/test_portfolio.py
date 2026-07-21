from pathlib import Path

import pytest

from compute_to_ai.engine.effect import ComputedEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_monte_carlo, run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline
from compute_to_ai.features.finance.portfolio import (
    add_asset_class,
    add_cash_bucket,
    add_portfolio_rebalancing,
    set_correlation_matrix,
    suggest_contribution_allocation,
)
from compute_to_ai.features.finance.position import add_position
from compute_to_ai.features.finance.positions_rebalancing import add_position_rebalancing
from compute_to_ai.mcp.tools.plan_storage import load_plan, plan_file, save_plan


def test_add_portfolio_rebalancing_rejects_unknown_weight_keys() -> None:
    plan = Plan(
        name="rebalance-unknown-store",
        timeline=Timeline(step_count=1),
        stores=[Store(name="equity", balance=70.0)],
    )

    # Both unknown keys must appear in the message, not just the first one.
    with pytest.raises(ValueError, match=r"\['bondd', 'equityy'\]"):
        add_portfolio_rebalancing(
            plan=plan,
            name="Portfolio Rebalancing",
            weights={"equityy": 0.70, "bondd": 0.30},
        )
    assert plan.effects == []


def test_add_cash_bucket_rejects_unknown_portfolio_weight_key() -> None:
    plan = Plan(
        name="cash-bucket-unknown-weight-key",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
    )

    with pytest.raises(ValueError, match="stockss"):
        add_cash_bucket(
            plan=plan,
            portfolio_weights={"stockss": 1.0},
            emergency_buffer_months={},
            monthly_expenses=1000.0,
        )
    assert plan.effects == []


def test_add_cash_bucket_rejects_unknown_cash_store_name() -> None:
    """A typo'd cash_store_name must fail instead of silently creating a
    phantom store (the former auto-create behavior)."""
    plan = Plan(
        name="cash-bucket-unknown-cash-store",
        timeline=Timeline(step_count=1),
        stores=[Store(name="stocks", balance=100.0)],
    )

    with pytest.raises(ValueError, match="kasse"):
        add_cash_bucket(
            plan=plan,
            portfolio_weights={"stocks": 1.0},
            emergency_buffer_months={},
            monthly_expenses=1000.0,
            cash_store_name="kasse",
        )

    # No partial state: no phantom store, no effect.
    assert [store.name for store in plan.stores] == ["stocks"]
    assert plan.effects == []


def test_portfolio_rebalancing_deterministic() -> None:
    plan = Plan(
        name="rebalance-deterministic",
        timeline=Timeline(step_count=2),
        stores=[],
    )

    # Add asset classes using the helper
    add_asset_class(
        plan=plan,
        store_name="equity",
        initial_balance=70.0,
        expected_return=0.20,
        volatility=0.15,
    )
    add_asset_class(
        plan=plan,
        store_name="bond",
        initial_balance=30.0,
        expected_return=0.10,
        volatility=0.05,
    )

    # Add rebalancing computed effect
    add_portfolio_rebalancing(
        plan=plan,
        name="Portfolio Rebalancing",
        weights={"equity": 0.70, "bond": 0.30},
    )

    result = run_simulation(plan)

    # Step 0:
    # Phase 1: equity grows by 20% to 84.0. bond grows by 10% to 33.0.
    # Total portfolio = 84 + 33 = 117.
    # Phase 2: rebalanced to 70/30.
    # equity target: 117 * 0.70 = 81.9
    # bond target: 117 * 0.30 = 35.1
    assert pytest.approx(result.time_series[0]["equity"]) == 81.9
    assert pytest.approx(result.time_series[0]["bond"]) == 35.1

    # Step 1:
    # Phase 1:
    # equity grows by 20%: 81.9 * 1.2 = 98.28.
    # bond grows by 10%: 35.1 * 1.1 = 38.61.
    # Total portfolio = 98.28 + 38.61 = 136.89.
    # Phase 2: rebalanced to 70/30.
    # equity target: 136.89 * 0.70 = 95.823
    # bond target: 136.89 * 0.30 = 41.067
    assert pytest.approx(result.final_balances["equity"]) == 95.823
    assert pytest.approx(result.final_balances["bond"]) == 41.067


def test_portfolio_rebalancing_stochastic() -> None:
    plan = Plan(
        name="rebalance-stochastic",
        timeline=Timeline(step_count=3),
        stores=[],
    )

    add_asset_class(
        plan=plan,
        store_name="equity",
        initial_balance=70.0,
        expected_return=0.07,
        volatility=0.15,
    )
    add_asset_class(
        plan=plan,
        store_name="bond",
        initial_balance=30.0,
        expected_return=0.03,
        volatility=0.05,
    )

    # Set correlation matrix
    set_correlation_matrix(
        plan=plan,
        group_name="portfolio",
        matrix=[[1.0, -0.2], [-0.2, 1.0]],
        store_names=["equity", "bond"],
    )

    # Add rebalancing computed effect
    add_portfolio_rebalancing(
        plan=plan,
        name="Rebalancing",
        weights={"equity": 0.70, "bond": 0.30},
    )

    # Run Monte Carlo
    mc_result = run_monte_carlo(plan, num_runs=5, seed=42)

    # In every run, the final proportion of equity / bond must be exactly 70 / 30
    for final_bal in mc_result.raw_final_balances:
        eq_final = final_bal["equity"]
        bd_final = final_bal["bond"]
        total = eq_final + bd_final
        assert pytest.approx(eq_final / total) == 0.70
        assert pytest.approx(bd_final / total) == 0.30


def test_single_asset_class_without_correlation_matrix_is_still_stochastic() -> None:
    """A single asset class must stay stochastic even if the caller never calls
    set_correlation_matrix - an unconfigured correlation group must not silently
    fall back to the deterministic expected_return (see Docs/Auffaelligkeiten.md-
    style dogfooding feedback: this previously produced identical Monte-Carlo
    runs with zero variance).
    """
    plan = Plan(
        name="single-asset-class-stochastic",
        timeline=Timeline(step_count=10),
        stores=[],
    )

    add_asset_class(
        plan=plan,
        store_name="etf",
        initial_balance=10000.0,
        expected_return=0.07,
        volatility=0.15,
    )

    mc_result = run_monte_carlo(plan, num_runs=20, seed=42)

    final_values = [bal["etf"] for bal in mc_result.raw_final_balances]
    assert len(set(final_values)) > 1


def test_cash_bucket_excess_moves_to_portfolio() -> None:
    from compute_to_ai.engine.timeline import Phase

    plan = Plan(
        name="cash-bucket-excess-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=100.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(plan, "equity", 0.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 0.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Erwerbsphase": 3.0},
        monthly_expenses=10.0,
    )

    result = run_simulation(plan)

    # Target Cash is 3.0 * 10 = 30. Excess is 70.
    # Equity gets 49, Bond gets 21. Cash stays at 30.
    assert pytest.approx(result.final_balances["cash"]) == 30.0
    assert pytest.approx(result.final_balances["equity"]) == 49.0
    assert pytest.approx(result.final_balances["bond"]) == 21.0


def test_cash_bucket_caps_target_at_max() -> None:
    from compute_to_ai.engine.timeline import Phase

    plan = Plan(
        name="cash-bucket-max-target-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=100.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(plan, "equity", 0.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 0.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Erwerbsphase": 3.0},
        monthly_expenses=10.0,
        max_target_cash=10.0,
    )

    result = run_simulation(plan)

    # Computed target would be 30, but max_target_cash=10 caps it - the
    # excess above 10 (not just above 30) sweeps to the portfolio.
    assert pytest.approx(result.final_balances["cash"]) == 10.0
    assert pytest.approx(result.final_balances["equity"]) == 63.0
    assert pytest.approx(result.final_balances["bond"]) == 27.0


def test_cash_bucket_max_target_has_no_effect_when_above_computed_target() -> None:
    from compute_to_ai.engine.timeline import Phase

    plan = Plan(
        name="cash-bucket-max-target-noop-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=100.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(plan, "equity", 0.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 0.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Erwerbsphase": 3.0},
        monthly_expenses=10.0,
        max_target_cash=1000.0,
    )

    result = run_simulation(plan)

    # Cap (1000) is above the computed target (30) - identical to the
    # uncapped case.
    assert pytest.approx(result.final_balances["cash"]) == 30.0
    assert pytest.approx(result.final_balances["equity"]) == 49.0
    assert pytest.approx(result.final_balances["bond"]) == 21.0


def test_cash_bucket_deficit_pulls_from_portfolio() -> None:
    from compute_to_ai.engine.timeline import Phase

    plan = Plan(
        name="cash-bucket-deficit-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(plan, "equity", 70.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 30.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Erwerbsphase": 3.0},
        monthly_expenses=10.0,
    )

    result = run_simulation(plan)

    # Target Cash is 30. Deficit is 30.
    # equity has 70.0 - 21.0 = 49.0
    # bond has 30.0 - 9.0 = 21.0
    assert pytest.approx(result.final_balances["cash"]) == 30.0
    assert pytest.approx(result.final_balances["equity"]) == 49.0
    assert pytest.approx(result.final_balances["bond"]) == 21.0


def test_cash_bucket_with_near_horizon_expenses() -> None:
    from compute_to_ai.engine.timeline import Phase
    from compute_to_ai.features.finance.cashflow import add_fixed_acquisition

    plan = Plan(
        name="cash-bucket-near-horizon-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=100.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=10)],
    )

    add_asset_class(plan, "equity", 0.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 0.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Erwerbsphase": 3.0},
        monthly_expenses=10.0,
        near_horizon_steps=2,
    )

    # Add a fixed acquisition at step 2 of amount 50
    add_fixed_acquisition(plan, "Car", "cash", amount=50.0, step=2)

    result = run_simulation(plan)

    # At step 0:
    # Buffer 1: 3 * 10 = 30
    # Buffer 2: fixed acquisition of 50 at step 2 falls in near-horizon (s=1,2).
    # Buffer 2 is 50.
    # Total Target Cash is 80. Excess is 20.
    # Equity gets 14, Bond gets 6. Cash stays at 80.
    assert pytest.approx(result.time_series[0]["cash"]) == 80.0
    assert pytest.approx(result.time_series[0]["equity"]) == 14.0
    assert pytest.approx(result.time_series[0]["bond"]) == 6.0


def test_cash_bucket_entnahme_buffer_ignores_phase_name() -> None:
    """The Entnahmepuffer component must fire purely via `withdrawal_phase_names`.

    The phase is deliberately named "Ruhestand" rather than "Rentenphase" to prove
    genericity: nothing about the phase's name is special-cased.
    """
    from compute_to_ai.engine.effect import GrowingFixedEffect
    from compute_to_ai.engine.timeline import Phase

    plan = Plan(
        name="cash-bucket-entnahme-test",
        timeline=Timeline(step_count=1, steps_per_year=1),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Ruhestand", start_step=0, end_step=10)],
        effects=[GrowingFixedEffect(name="Ausgaben", store_name="cash", amount_per_step=-1000.0)],
    )

    add_asset_class(plan, "equity", 4000.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 2000.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Ruhestand": 0.0},
        monthly_expenses=0.0,
        withdrawal_years=3.0,
        withdrawal_phase_names=["Ruhestand"],
    )

    result = run_simulation(plan)

    # Entnahmeabhängigkeit = (1000 - 0) / 1000 = 1.0 (no offsetting income).
    # Entnahmepuffer = 3 Jahre * 1.0 * 1000 = 3000. Deficit vs. cash (-1000) = 4000.
    # Portfolio (6000) covers it: equity -= 4000*0.7=2800, bond -= 4000*0.3=1200.
    assert pytest.approx(result.final_balances["cash"]) == 3000.0
    assert pytest.approx(result.final_balances["equity"]) == 1200.0
    assert pytest.approx(result.final_balances["bond"]) == 800.0


def test_cash_bucket_entnahme_buffer_is_step_granularity_invariant() -> None:
    """The same yearly expenses and withdrawal_years must yield the same
    Entnahmepuffer amount on a monthly-step plan as on an annual-step plan -
    the buffer means "N years of expected net expenses", not "N steps".
    """
    from compute_to_ai.engine.effect import GrowingFixedEffect
    from compute_to_ai.engine.timeline import Phase

    def _final_cash(steps_per_year: int, expense_per_step: float) -> float:
        plan = Plan(
            name=f"cash-bucket-entnahme-invariance-{steps_per_year}",
            timeline=Timeline(step_count=1, steps_per_year=steps_per_year),
            stores=[Store(name="cash", balance=0.0)],
            phases=[Phase(name="Ruhestand", start_step=0, end_step=100)],
            effects=[
                GrowingFixedEffect(
                    name="Ausgaben", store_name="cash", amount_per_step=expense_per_step
                )
            ],
        )
        add_asset_class(plan, "equity", 40000.0, 0.0, 0.0)
        add_asset_class(plan, "bond", 20000.0, 0.0, 0.0)
        add_cash_bucket(
            plan=plan,
            portfolio_weights={"equity": 0.70, "bond": 0.30},
            emergency_buffer_months={"Ruhestand": 0.0},
            monthly_expenses=0.0,
            withdrawal_years=3.0,
            withdrawal_phase_names=["Ruhestand"],
        )
        result = run_simulation(plan)
        return result.final_balances["cash"]

    # 12,000/year of expenses either way: -12,000 per annual step, or
    # -1,000 per monthly step. Buffer = 3 years * 12,000 = 36,000 in both.
    assert pytest.approx(_final_cash(1, -12000.0)) == 36000.0
    assert pytest.approx(_final_cash(12, -1000.0)) == 36000.0


def test_cash_bucket_entnahme_buffer_skips_unlisted_phase() -> None:
    """A phase not listed in `withdrawal_phase_names` never contributes the buffer,
    even if it happens to be named "Rentenphase".
    """
    from compute_to_ai.engine.effect import GrowingFixedEffect
    from compute_to_ai.engine.timeline import Phase

    plan = Plan(
        name="cash-bucket-entnahme-skip-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Rentenphase", start_step=0, end_step=10)],
        effects=[GrowingFixedEffect(name="Ausgaben", store_name="cash", amount_per_step=-1000.0)],
    )

    add_asset_class(plan, "equity", 4000.0, 0.0, 0.0)
    add_asset_class(plan, "bond", 2000.0, 0.0, 0.0)

    add_cash_bucket(
        plan=plan,
        portfolio_weights={"equity": 0.70, "bond": 0.30},
        emergency_buffer_months={"Rentenphase": 0.0},
        monthly_expenses=0.0,
        withdrawal_years=3.0,
        withdrawal_phase_names=[],
    )

    result = run_simulation(plan)

    # No withdrawal_phase_names configured -> Entnahmepuffer contributes 0, so
    # target cash is 0 (buffer_1/buffer_2 are 0 too). The expense drove cash to
    # -1000; the manager still reconciles cash to the (lower) target of 0 by
    # pulling 1000 from the portfolio: equity -= 1000*0.7=700, bond -= 1000*0.3=300.
    assert pytest.approx(result.final_balances["cash"]) == 0.0
    assert pytest.approx(result.final_balances["equity"]) == 3300.0
    assert pytest.approx(result.final_balances["bond"]) == 1700.0


def _plan_with_single_and_multi_position_asset_classes() -> Plan:
    """One single-position asset class ("bond") and one multi-position asset
    class ("equity_active" + sibling "equity_sibling"), both valued but
    without a portfolio_rebalancing effect - callers add their own weights.
    """
    plan = Plan(name="contribution-allocation-test", timeline=Timeline(step_count=1), stores=[])

    add_asset_class(plan, "equity_active", 700.0, 0.0, 0.0)
    add_position(plan, "equity_active", "equity_sibling")
    plan.store("equity_sibling").balance = 300.0
    add_position_rebalancing(plan, ["equity_active", "equity_sibling"], "equity_active")

    add_asset_class(plan, "bond", 1000.0, 0.0, 0.0)

    return plan


def test_suggest_contribution_allocation_is_group_aware() -> None:
    plan = _plan_with_single_and_multi_position_asset_classes()
    add_portfolio_rebalancing(
        plan=plan,
        name="Portfolio Rebalancing",
        weights={"equity_active": 0.6, "bond": 0.4},
    )

    suggestions = suggest_contribution_allocation(plan, new_amount=1000.0)
    by_store = {s.store_name: s for s in suggestions}

    # equity_active's bucket uses the *whole group's* balance (700 + 300 = 1000),
    # not just the active store's own 700.
    assert by_store["equity_active"].current_value == pytest.approx(1000.0)
    assert by_store["equity_active"].suggested_contribution == pytest.approx(800.0)
    assert by_store["equity_active"].warning is None

    assert by_store["bond"].current_value == pytest.approx(1000.0)
    assert by_store["bond"].suggested_contribution == pytest.approx(200.0)
    assert by_store["bond"].warning is None

    total = sum(s.suggested_contribution for s in suggestions)
    assert total == pytest.approx(1000.0)


def test_suggest_contribution_allocation_is_genuinely_read_only(tmp_path: Path) -> None:
    plan = _plan_with_single_and_multi_position_asset_classes()
    add_portfolio_rebalancing(
        plan=plan,
        name="Portfolio Rebalancing",
        weights={"equity_active": 0.6, "bond": 0.4},
    )
    save_plan(tmp_path, plan)
    file = plan_file(tmp_path, plan.name)
    before_bytes = file.read_bytes()

    loaded_plan = load_plan(tmp_path, plan.name)
    suggest_contribution_allocation(loaded_plan, new_amount=1000.0)

    assert file.read_bytes() == before_bytes
    assert loaded_plan.store("equity_active").balance == pytest.approx(700.0)
    assert loaded_plan.store("equity_sibling").balance == pytest.approx(300.0)
    assert loaded_plan.store("bond").balance == pytest.approx(1000.0)


def test_suggest_contribution_allocation_requires_portfolio_rebalancing() -> None:
    plan = Plan(name="no-rebalancing", timeline=Timeline(step_count=1), stores=[])
    add_asset_class(plan, "equity", 1000.0, 0.0, 0.0)

    with pytest.raises(ValueError, match="portfolio_rebalancing"):
        suggest_contribution_allocation(plan, new_amount=100.0)


def test_suggest_contribution_allocation_warns_on_active_position_mismatch() -> None:
    plan = _plan_with_single_and_multi_position_asset_classes()
    # Misconfigured on purpose: the weights key points at the sibling, not
    # the position actually marked active by add_position_rebalancing above.
    plan.effects = [
        effect
        for effect in plan.effects
        if not (
            isinstance(effect, ComputedEffect) and effect.function_name == "portfolio_rebalancing"
        )
    ]
    add_portfolio_rebalancing(
        plan=plan,
        name="Portfolio Rebalancing",
        weights={"equity_sibling": 0.6, "bond": 0.4},
    )

    suggestions = suggest_contribution_allocation(plan, new_amount=1000.0)
    by_store = {s.store_name: s for s in suggestions}

    assert by_store["equity_sibling"].warning is not None
    assert "equity_active" in by_store["equity_sibling"].warning
    assert by_store["bond"].warning is None
