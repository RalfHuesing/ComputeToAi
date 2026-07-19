"""Tests for position.py - see Docs/03-Feature-Finanzen-Domaenenmodell.md, "Position"."""

from datetime import date

import pytest

from compute_to_ai.engine.store import Store
from compute_to_ai.features.finance.position import (
    PositionTransaction,
    apply_price_update,
    apply_transaction_history,
    set_position_balance,
)


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


def test_apply_transaction_history_builds_one_lot_per_buy_in_order() -> None:
    store = Store(name="equity")
    transactions = [
        PositionTransaction(date=date(2020, 1, 1), shares=10.0, price=100.0),
        PositionTransaction(date=date(2021, 1, 1), shares=5.0, price=120.0),
    ]

    apply_transaction_history(store, transactions)

    assert store.balance == pytest.approx(10 * 100.0 + 5 * 120.0)
    assert len(store.lots) == 2
    assert store.lots[0].quantity == pytest.approx(1000.0)
    assert store.lots[0].cost_basis == pytest.approx(1000.0)
    assert store.lots[1].quantity == pytest.approx(600.0)
    assert store.lots[1].cost_basis == pytest.approx(600.0)


def test_apply_transaction_history_sell_consumes_earliest_lot_first() -> None:
    store = Store(name="equity")
    transactions = [
        PositionTransaction(date=date(2020, 1, 1), shares=10.0, price=100.0),
        PositionTransaction(date=date(2021, 1, 1), shares=5.0, price=120.0),
        PositionTransaction(date=date(2022, 1, 1), shares=-4.0),
    ]

    apply_transaction_history(store, transactions)

    # withdraw_amount is called with the raw sold share count (4.0), which
    # is subtracted from the first (earliest, FIFO) lot's currency quantity.
    assert len(store.lots) == 2
    assert store.lots[0].quantity == pytest.approx(1000.0 - 4.0)
    assert store.lots[0].cost_basis == pytest.approx(1000.0 - 4.0)
    assert store.lots[1].quantity == pytest.approx(600.0)
    assert store.balance == pytest.approx(1000.0 - 4.0 + 600.0)


def test_apply_transaction_history_marks_pre_2009_lot() -> None:
    store = Store(name="equity")
    transactions = [
        PositionTransaction(date=date(2008, 6, 1), shares=10.0, price=50.0),
        PositionTransaction(date=date(2010, 6, 1), shares=5.0, price=80.0),
    ]

    apply_transaction_history(store, transactions)

    assert store.lots[0].rule_version == "pre_2009"
    assert store.lots[1].rule_version is None


def test_apply_transaction_history_replaces_existing_lots() -> None:
    store = Store(name="equity")
    set_position_balance(store, shares=100.0, price=1.0, step=0)

    apply_transaction_history(
        store, [PositionTransaction(date=date(2020, 1, 1), shares=1.0, price=10.0)]
    )

    assert len(store.lots) == 1
    assert store.balance == pytest.approx(10.0)


def test_apply_transaction_history_rejects_buy_without_price() -> None:
    store = Store(name="equity")

    with pytest.raises(ValueError, match="price"):
        apply_transaction_history(
            store, [PositionTransaction(date=date(2020, 1, 1), shares=1.0, price=None)]
        )


def test_apply_transaction_history_rejects_buy_with_non_positive_price() -> None:
    store = Store(name="equity")

    with pytest.raises(ValueError, match="price"):
        apply_transaction_history(
            store, [PositionTransaction(date=date(2020, 1, 1), shares=1.0, price=0.0)]
        )
