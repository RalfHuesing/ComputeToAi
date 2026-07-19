"""Tests for position.py - see Docs/03-Feature-Finanzen-Domaenenmodell.md, "Position"."""

import pytest

from compute_to_ai.engine.store import Store
from compute_to_ai.features.finance.position import apply_price_update, set_position_balance


def test_set_position_balance_on_empty_store() -> None:
    store = Store(name="equity")

    set_position_balance(store, shares=10.0, price=100.0, step=3)

    assert store.balance == pytest.approx(1000.0)
    assert len(store.lots) == 1
    assert store.lots[0].quantity == pytest.approx(1000.0)
    assert store.lots[0].cost_basis == pytest.approx(1000.0)
    assert store.lots[0].created_step == 3


def test_set_position_balance_replaces_existing_position() -> None:
    store = Store(name="equity")
    set_position_balance(store, shares=10.0, price=100.0, step=0)

    set_position_balance(store, shares=5.0, price=50.0, step=0)

    assert store.balance == pytest.approx(250.0)
    assert len(store.lots) == 1
    assert store.lots[0].cost_basis == pytest.approx(250.0)
    assert store.withdrawn_lots_this_step == []


def test_apply_price_update_on_price_increase_preserves_cost_basis() -> None:
    store = Store(name="equity")
    set_position_balance(store, shares=10.0, price=100.0, step=0)

    apply_price_update(store, shares=10.0, new_price=120.0)

    assert store.balance == pytest.approx(1200.0)
    assert len(store.lots) == 1
    assert store.lots[0].cost_basis == pytest.approx(1000.0)


def test_apply_price_update_on_price_decrease_preserves_cost_basis() -> None:
    store = Store(name="equity")
    set_position_balance(store, shares=10.0, price=100.0, step=0)

    apply_price_update(store, shares=10.0, new_price=80.0)

    assert store.balance == pytest.approx(800.0)
    assert len(store.lots) == 1
    assert store.lots[0].cost_basis == pytest.approx(1000.0)


def test_apply_price_update_on_empty_store_falls_back_to_set_position_balance() -> None:
    store = Store(name="equity")

    apply_price_update(store, shares=10.0, new_price=100.0)

    assert store.balance == pytest.approx(1000.0)
    assert store.lots[0].cost_basis == pytest.approx(1000.0)
