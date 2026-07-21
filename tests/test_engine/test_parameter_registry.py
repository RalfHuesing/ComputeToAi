"""Tests for plan parameter registry and dynamic rate reference resolution."""

import pytest

from compute_to_ai.engine.effect import GrowingFixedEffect, PercentageGrowthEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline


def test_plan_parameter_set_and_resolve() -> None:
    """Test setting parameters on Plan and resolving rate values."""
    plan = Plan(name="test_plan", timeline=Timeline(step_count=5))
    plan.set_parameter("inflation_general", 0.025)

    assert plan.parameters["inflation_general"] == 0.025
    assert plan.resolve_rate(0.02) == 0.02
    assert plan.resolve_rate("0.02") == 0.02
    assert plan.resolve_rate("ref:inflation_general") == 0.025


def test_resolve_rate_missing_reference_raises_value_error() -> None:
    """Test that resolving an undefined parameter reference raises a ValueError."""
    plan = Plan(name="test_plan", timeline=Timeline(step_count=5))
    with pytest.raises(ValueError, match="is not defined in plan 'test_plan'"):
        plan.resolve_rate("ref:missing_param")


def test_effect_parameter_resolution_in_simulation() -> None:
    """Test dynamic simulation response when changing a central parameter."""
    plan = Plan(
        name="sim_test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="Girokonto", balance=1000.0)],
        effects=[
            GrowingFixedEffect(
                store_name="Girokonto",
                amount_per_step=100.0,
                growth_rate="ref:inflation_general",
            ),
            PercentageGrowthEffect(
                store_names=["Girokonto"],
                growth_rate="ref:inflation_general",
            ),
        ],
        parameters={"inflation_general": 0.02},
    )

    result_low = run_simulation(plan)

    # Change central parameter to 0.10
    plan.set_parameter("inflation_general", 0.10)
    result_high = run_simulation(plan)

    # Balance after step 2 should be higher with 10% rate than with 2% rate
    assert result_high.final_balances["Girokonto"] > result_low.final_balances["Girokonto"]
