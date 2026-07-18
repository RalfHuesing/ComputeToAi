from compute_to_ai.engine.effect import FixedEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline


def test_run_simulation_applies_effect_at_every_step() -> None:
    plan = Plan(
        name="two-steps",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=0.0)],
        effects=[FixedEffect(store_name="cash", amount_per_step=10.0)],
    )

    result = run_simulation(plan)

    assert result.final_balances == {"cash": 20.0}
    assert result.time_series == [{"cash": 10.0}, {"cash": 20.0}]


def test_run_simulation_leaves_stores_without_effects_unchanged() -> None:
    plan = Plan(
        name="no-effects",
        timeline=Timeline(step_count=5),
        stores=[Store(name="cash", balance=100.0)],
    )

    result = run_simulation(plan)

    assert result.final_balances == {"cash": 100.0}


def test_golden_100_euro_per_month_zero_return_40_years() -> None:
    """100 €/month, 0 % return, 40 years (480 months) -> 48,000 €."""
    plan = Plan(
        name="retirement-baseline",
        timeline=Timeline(step_count=480),
        stores=[Store(name="portfolio", balance=0.0)],
        effects=[FixedEffect(store_name="portfolio", amount_per_step=100.0)],
    )

    result = run_simulation(plan)

    assert result.final_balances["portfolio"] == 48_000.0
