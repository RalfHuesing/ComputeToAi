import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_monte_carlo, run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline
from compute_to_ai.features.finance.cashflow import (
    add_expense,
    add_fixed_acquisition,
    add_flexible_acquisition,
    add_income_stream,
)


def test_add_income_and_expense() -> None:
    plan = Plan(
        name="income-expense-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=1000.0)],
    )

    # Income: base 500, grows at 5% p.a.
    add_income_stream(plan, "Salary", "cash", amount=500.0, growth_rate=0.05)

    # Expense: base 300, inflates at 2% p.a.
    add_expense(plan, "Rent", "cash", amount=300.0, inflation_rate=0.02)

    result = run_simulation(plan)

    # Step 0:
    # Income grows to 500
    # Expense grows to -300
    # Cash becomes 1000 plus 500 minus 300 which is 1200
    #
    # Step 1:
    # Income grows to 525
    # Expense grows to -306
    # Cash becomes 1200 plus 525 minus 306 which is 1419
    assert pytest.approx(result.final_balances["cash"]) == 1419.0
    assert result.time_series == [{"cash": 1200.0}, {"cash": 1419.0}]


def test_add_income_stream_rejects_unknown_phase_name() -> None:
    plan = Plan(
        name="income-unknown-phase-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=1)],
    )

    with pytest.raises(ValueError, match="work"):
        add_income_stream(plan, "Salary", "cash", amount=500.0, active_phases=["work"])


def test_add_expense_rejects_unknown_phase_name() -> None:
    plan = Plan(
        name="expense-unknown-phase-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=0.0)],
        phases=[Phase(name="Erwerbsphase", start_step=0, end_step=1)],
    )

    with pytest.raises(ValueError, match="work"):
        add_expense(plan, "Rent", "cash", amount=300.0, active_phases=["work"])


def test_add_fixed_acquisition() -> None:
    plan = Plan(
        name="fixed-acquisition-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=1000.0)],
    )

    # One-time fixed acquisition of 500 at step 1, with 10% inflation
    add_fixed_acquisition(plan, "Car", "cash", amount=500.0, step=1, inflation_rate=0.10)

    result = run_simulation(plan)

    # Step 0: acquisition is not active. Cash remains 1000
    # Step 1: acquisition is active. Nominal cost is 550
    # Cash becomes 1000 minus 550 which is 450
    assert pytest.approx(result.final_balances["cash"]) == 450.0
    assert result.time_series == [{"cash": 1000.0}, {"cash": 450.0}]


def test_add_fixed_acquisition_ignores_a_pre_negated_amount() -> None:
    """amount is always a magnitude - passing it already-negative must not
    double-negate into an inflow (a real usability trap found in dogfooding:
    a caller reasonably assumes "acquisition" wants a negative amount)."""
    plan = Plan(
        name="fixed-acquisition-negative-input-test",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=1000.0)],
    )

    add_fixed_acquisition(plan, "Car", "cash", amount=-500.0, step=0)

    result = run_simulation(plan)

    assert pytest.approx(result.final_balances["cash"]) == 500.0


def test_add_flexible_acquisition_ignores_a_pre_negated_amount() -> None:
    """amount is always a magnitude, matching add_fixed_acquisition's
    convention - a pre-negated input must not flip the acquisition into an
    inflow."""
    plan = Plan(
        name="flex-acq-negative-input-test",
        timeline=Timeline(step_count=1),
        stores=[
            Store(name="portfolio", balance=0.0),
            Store(name="cash", balance=1000.0),
        ],
    )

    add_flexible_acquisition(
        plan=plan,
        name="Boat",
        amount=-120.0,
        target_step=0,
        tolerance_steps=0,
        risky_store_name="portfolio",
        safe_store_name="cash",
        glidepath_start_step=0,
        inflation_rate=0.0,
    )

    result = run_simulation(plan)

    assert pytest.approx(result.final_balances["cash"]) == 880.0


def test_flexible_acquisition_triggers_on_refpath() -> None:
    # Portfolio starts at 100, grows by 20% each step.
    # We want to buy an item of nominal cost 120 at step 5 (window [3, 7]).
    # Since the portfolio grows, it will hit the trigger condition early.
    plan = Plan(
        name="flex-acq-refpath",
        timeline=Timeline(step_count=8),
        stores=[
            Store(name="portfolio", balance=100.0),
            Store(name="cash", balance=0.0),
        ],
    )

    # Add growth on portfolio: +20% per step
    from compute_to_ai.engine.effect import PercentageGrowthEffect
    plan.effects.append(PercentageGrowthEffect(store_name="portfolio", growth_rate=0.20))

    # Add flexible acquisition
    add_flexible_acquisition(
        plan=plan,
        name="Boat",
        amount=120.0,
        target_step=5,
        tolerance_steps=2,
        risky_store_name="portfolio",
        safe_store_name="cash",
        glidepath_start_step=2,
        inflation_rate=0.0,
    )

    result = run_simulation(plan)

    # Without trigger, it would grow to 100 * 1.2^8 = 429.98.
    # With trigger at step 3, portfolio is 87.36 at end of step 3, then grows for 4 more steps.
    # Expected value is 181.10 (87.36 * 1.2^4)
    assert pytest.approx(result.final_balances["portfolio"], 1e-2) == 181.10
    assert result.final_balances["cash"] == 0.0


def test_flexible_acquisition_triggers_on_deadline() -> None:
    # Portfolio has 0% growth, cash has 0% growth.
    # Total capital is 50. Boat cost is 120.
    # Target step: 5, tolerance: 2 (window [3, 7]).
    # Reference path at step 3 is 72. Since 50 < 72, it won't trigger.
    # It must trigger at step 7 (hard deadline).
    plan = Plan(
        name="flex-acq-deadline",
        timeline=Timeline(step_count=9),
        stores=[
            Store(name="portfolio", balance=50.0),
            Store(name="cash", balance=0.0),
        ],
    )

    add_flexible_acquisition(
        plan=plan,
        name="Boat",
        amount=120.0,
        target_step=5,
        tolerance_steps=2,
        risky_store_name="portfolio",
        safe_store_name="cash",
        glidepath_start_step=2,
        inflation_rate=0.0,
    )

    result = run_simulation(plan)

    # Safe target at step 2 (glidepath starts): 0.
    # At step 3: safe target is 120. Shift max available (50) to cash.
    # portfolio becomes 0, cash becomes 50.
    # At step 3-6: ref path is always > 50, so no trigger.
    # At step 7 (deadline): triggers!
    # Deducts 120. cash (50) is reduced to 0. Remaining 70 is deducted
    # from portfolio which is 0 minus 70 and then capped at 0.
    # Cash becomes 0, portfolio becomes 0.
    assert result.final_balances["portfolio"] == 0.0
    assert result.final_balances["cash"] == 0.0


def test_flexible_acquisition_trigger_does_not_leak_across_monte_carlo_runs() -> None:
    """A ComputedEffect's `parameters` dict is run-scoped state, not shared across runs.

    `flexible_acquisition_func` marks itself triggered by writing into its own
    `parameters` dict. Without a fresh per-run copy of `plan.effects`, that
    write would persist into every subsequent Monte-Carlo run, permanently
    disabling the acquisition after the first run it fires in.
    """
    plan = Plan(
        name="flex-acq-monte-carlo",
        timeline=Timeline(step_count=8),
        stores=[
            Store(name="portfolio", balance=100.0),
            Store(name="cash", balance=0.0),
        ],
    )

    from compute_to_ai.engine.effect import PercentageGrowthEffect

    plan.effects.append(PercentageGrowthEffect(store_name="portfolio", growth_rate=0.20))

    add_flexible_acquisition(
        plan=plan,
        name="Boat",
        amount=120.0,
        target_step=5,
        tolerance_steps=2,
        risky_store_name="portfolio",
        safe_store_name="cash",
        glidepath_start_step=2,
        inflation_rate=0.0,
    )

    mc_result = run_monte_carlo(plan, num_runs=5, seed=1)

    # Fully deterministic plan (no stochastic effects) - every run must trigger
    # identically and land on the same final balance.
    for final_bal in mc_result.raw_final_balances:
        assert pytest.approx(final_bal["portfolio"], 1e-2) == 181.10
        assert final_bal["cash"] == 0.0
