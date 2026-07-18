import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline


def _plan() -> Plan:
    return Plan(
        name="test-plan",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=10.0)],
    )


def test_store_returns_matching_store() -> None:
    plan = _plan()

    assert plan.store("cash").balance == 10.0


def test_store_raises_for_unknown_name() -> None:
    plan = _plan()

    with pytest.raises(KeyError):
        plan.store("unknown")
