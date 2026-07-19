import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline


def _plan(phases: list[Phase] | None = None) -> Plan:
    return Plan(
        name="test-plan",
        timeline=Timeline(step_count=1),
        stores=[Store(name="cash", balance=10.0)],
        phases=phases or [],
    )


def test_store_returns_matching_store() -> None:
    plan = _plan()

    assert plan.store("cash").balance == 10.0


def test_store_raises_for_unknown_name() -> None:
    plan = _plan()

    with pytest.raises(KeyError):
        plan.store("unknown")


def test_validate_active_phases_accepts_none() -> None:
    _plan().validate_active_phases(None)


def test_validate_active_phases_accepts_known_names() -> None:
    plan = _plan(phases=[Phase(name="Erwerbsphase", start_step=0, end_step=1)])

    plan.validate_active_phases(["Erwerbsphase"])


def test_validate_active_phases_rejects_unknown_name() -> None:
    plan = _plan(phases=[Phase(name="Erwerbsphase", start_step=0, end_step=1)])

    with pytest.raises(ValueError, match="work"):
        plan.validate_active_phases(["work"])
