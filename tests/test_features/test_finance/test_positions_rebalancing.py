"""Tests for positions_rebalancing.py - see Docs/04-Feature-Finanzen-Methodik.md,
"Positions-Rebalancing innerhalb einer Anlageklasse".
"""

import pytest

from compute_to_ai.engine.effect import ComputedEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.store import Lot, Store
from compute_to_ai.engine.timeline import Timeline
from compute_to_ai.features.finance.positions_rebalancing import (
    PositionsRebalancingParameters,
    add_position_rebalancing,
    positions_rebalancing_func,
)


def _store(
    name: str,
    balance: float,
    cost_basis: float | None = None,
    rule_version: str | None = None,
) -> Store:
    """A store with a single lot, so cost basis/protection are controllable."""
    cost = balance if cost_basis is None else cost_basis
    return Store(
        name=name,
        balance=balance,
        lots=[Lot(quantity=balance, created_step=0, cost_basis=cost, rule_version=rule_version)],
    )


def _plan(*stores: Store) -> Plan:
    return Plan(
        name="positions-rebalancing-test", timeline=Timeline(step_count=1), stores=list(stores)
    )


def _run(
    plan: Plan, balances: dict[str, float], params: PositionsRebalancingParameters
) -> dict[str, float]:
    positions_rebalancing_func(balances, 0, params.model_dump(), plan)
    return balances


def test_sell_threshold_none_leaves_drifted_position_untouched() -> None:
    plan = _plan(_store("a", 100.0), _store("b", 500.0))
    params = PositionsRebalancingParameters(
        store_names=["a", "b"],
        active_store_name="a",
        sell_threshold=None,
        initial_weights={"b": 0.1},
    )

    balances = _run(plan, {"a": 100.0, "b": 500.0}, params)

    assert balances == {"a": 100.0, "b": 500.0}


def test_sell_threshold_none_still_covers_negative_active_balance() -> None:
    plan = _plan(_store("a", 0.0), _store("b", 500.0))
    params = PositionsRebalancingParameters(
        store_names=["a", "b"],
        active_store_name="a",
        sell_threshold=None,
        initial_weights={"b": 0.1},
    )

    balances = _run(plan, {"a": -50.0, "b": 500.0}, params)

    assert balances["a"] == pytest.approx(0.0)
    assert balances["b"] == pytest.approx(450.0)


def test_sell_threshold_zero_corrects_any_drift() -> None:
    plan = _plan(_store("a", 100.0), _store("b", 150.0))
    params = PositionsRebalancingParameters(
        store_names=["a", "b"],
        active_store_name="a",
        sell_threshold=0.0,
        initial_weights={"b": 0.5},
    )

    # total=250, b's initial weight is 0.5 (125); it currently holds 150,
    # 25 above target - sell_threshold=0 means even this must be corrected.
    balances = _run(plan, {"a": 100.0, "b": 150.0}, params)

    assert balances["b"] == pytest.approx(125.0)
    assert balances["a"] == pytest.approx(125.0)


def test_sell_threshold_middle_value_ignores_small_drift_but_corrects_large_drift() -> None:
    plan = _plan(_store("a", 100.0), _store("b", 140.0))
    params = PositionsRebalancingParameters(
        store_names=["a", "b"],
        active_store_name="a",
        sell_threshold=0.1,
        initial_weights={"b": 0.5},
    )

    # total=240, b's weight is 140/240=0.5833, drift=0.0833 <= 0.1 -> no-op.
    balances = _run(plan, {"a": 100.0, "b": 140.0}, params)
    assert balances == {"a": 100.0, "b": 140.0}

    plan2 = _plan(_store("a", 100.0), _store("b", 160.0))
    params2 = PositionsRebalancingParameters(
        store_names=["a", "b"],
        active_store_name="a",
        sell_threshold=0.1,
        initial_weights={"b": 0.5},
    )
    # total=260, b's weight is 160/260=0.6154, drift=0.1154 > 0.1 -> corrects.
    # sell_amount = 160 - 0.5*260 = 30.
    balances2 = _run(plan2, {"a": 100.0, "b": 160.0}, params2)
    assert balances2["b"] == pytest.approx(130.0)
    assert balances2["a"] == pytest.approx(130.0)


def test_sell_threshold_never_buys_into_an_underweight_sibling() -> None:
    """An underweight sibling ('c') is never topped up - only the active
    position ever receives proceeds, even while an overweight sibling ('b')
    is being sold down.
    """
    plan = _plan(_store("a", 100.0), _store("b", 300.0), _store("c", 100.0))
    params = PositionsRebalancingParameters(
        store_names=["a", "b", "c"],
        active_store_name="a",
        sell_threshold=0.0,
        initial_weights={"b": 0.5, "c": 0.4},
    )

    # total=500. b: weight 0.6 vs initial 0.5 -> oversold to 250.
    # c: weight 0.2 vs initial 0.4 -> underweight, must stay untouched.
    balances = _run(plan, {"a": 100.0, "b": 300.0, "c": 100.0}, params)

    assert balances["c"] == pytest.approx(100.0)
    assert balances["b"] == pytest.approx(250.0)
    assert balances["a"] == pytest.approx(150.0)


def test_shortfall_cover_stops_once_covered_preferring_lowest_gain_sibling() -> None:
    """Between two unprotected siblings, the one with the lower unrealized
    gain % is drawn from first, and drawing stops the moment the shortfall
    is fully covered - the higher-gain sibling stays untouched.
    """
    active = _store("a", 0.0)
    low_gain = _store("low_gain", 120.0, cost_basis=100.0)  # 20% gain
    high_gain = _store("high_gain", 150.0, cost_basis=100.0)  # 50% gain
    plan = _plan(active, low_gain, high_gain)
    params = PositionsRebalancingParameters(
        store_names=["a", "low_gain", "high_gain"], active_store_name="a"
    )

    balances = _run(plan, {"a": -50.0, "low_gain": 120.0, "high_gain": 150.0}, params)

    assert balances["a"] == pytest.approx(0.0)
    assert balances["low_gain"] == pytest.approx(70.0)
    assert balances["high_gain"] == pytest.approx(150.0)


def test_shortfall_cover_reaches_protected_sibling_only_as_last_resort() -> None:
    """Once every unprotected sibling is exhausted, drawing a still-open
    shortfall from a protected sibling is a last resort, not skipped.
    """
    active = _store("a", 0.0)
    zero_gain = _store("zero_gain", 100.0, cost_basis=100.0)  # 0% gain
    high_gain = _store("high_gain", 200.0, cost_basis=100.0)  # 100% gain
    protected = _store("protected", 5000.0, cost_basis=100.0, rule_version="pre_2009")
    plan = _plan(active, zero_gain, high_gain, protected)
    params = PositionsRebalancingParameters(
        store_names=["a", "zero_gain", "high_gain", "protected"], active_store_name="a"
    )

    balances = _run(
        plan,
        {"a": -1000.0, "zero_gain": 100.0, "high_gain": 200.0, "protected": 5000.0},
        params,
    )

    # zero_gain (0%) drained first (100), then high_gain (100%, 200), the
    # remaining 700 shortfall only then drawn from the protected sibling.
    assert balances["zero_gain"] == pytest.approx(0.0)
    assert balances["high_gain"] == pytest.approx(0.0)
    assert balances["protected"] == pytest.approx(5000.0 - 700.0)
    assert balances["a"] == pytest.approx(0.0)


def test_sell_threshold_never_sells_a_protected_sibling() -> None:
    """A protected sibling stays untouched by job (b) no matter how far over
    threshold it drifts.
    """
    protected = _store("protected", 900.0, cost_basis=100.0, rule_version="pre_2009")
    plan = _plan(_store("a", 100.0), protected)
    params = PositionsRebalancingParameters(
        store_names=["a", "protected"],
        active_store_name="a",
        sell_threshold=0.0,
        initial_weights={"protected": 0.1},
    )

    # protected currently holds 90% of the group, initial weight was 10% -
    # massively over threshold, yet must stay untouched.
    balances = _run(plan, {"a": 100.0, "protected": 900.0}, params)

    assert balances == {"a": 100.0, "protected": 900.0}


def test_add_position_rebalancing_rejects_active_not_in_store_names() -> None:
    plan = _plan(_store("a", 100.0), _store("b", 100.0))

    with pytest.raises(ValueError, match="active_store_name"):
        add_position_rebalancing(plan, store_names=["a", "b"], active_store_name="c")


def test_add_position_rebalancing_rejects_unknown_store() -> None:
    plan = _plan(_store("a", 100.0))

    with pytest.raises(ValueError, match="no store named"):
        add_position_rebalancing(plan, store_names=["a", "b"], active_store_name="a")


def test_add_position_rebalancing_rejects_zero_value_group() -> None:
    plan = _plan(_store("a", 0.0), _store("b", 0.0))

    with pytest.raises(ValueError, match="total balance"):
        add_position_rebalancing(plan, store_names=["a", "b"], active_store_name="a")


def test_add_position_rebalancing_rejects_overlapping_effect() -> None:
    plan = _plan(_store("a", 100.0), _store("b", 100.0), _store("c", 100.0))
    add_position_rebalancing(plan, store_names=["a", "b"], active_store_name="a")

    with pytest.raises(ValueError, match="positions_rebalancing"):
        add_position_rebalancing(plan, store_names=["b", "c"], active_store_name="b")


def test_add_position_rebalancing_computes_initial_weights_from_current_balances() -> None:
    plan = _plan(_store("a", 300.0), _store("b", 700.0))

    add_position_rebalancing(
        plan, store_names=["a", "b"], active_store_name="a", sell_threshold=0.1
    )

    effect = plan.effects[0]
    assert isinstance(effect, ComputedEffect)
    assert effect.function_name == "positions_rebalancing"
    assert effect.parameters["initial_weights"] == pytest.approx({"b": 0.7})
    assert effect.order == 5
