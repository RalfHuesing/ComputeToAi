"""Unit tests for Store and Lot - see Docs/01-Kern-Domaenenmodell.md."""

import pytest

from compute_to_ai.engine.store import Lot, Store


def test_add_amount_without_lots_uses_plain_balance() -> None:
    store = Store(name="cash", balance=100.0)
    store.add_amount(50.0, step=0)

    assert store.balance == 150.0
    assert store.lots == []


def test_add_amount_creates_lot_once_tracking_is_active() -> None:
    store = Store(name="portfolio", balance=0.0)
    store.add_amount(100.0, step=0, track_lots=True, cost_basis=100.0)
    store.add_amount(50.0, step=1, cost_basis=50.0)

    assert store.balance == 150.0
    assert [lot.quantity for lot in store.lots] == [100.0, 50.0]


def test_withdraw_amount_consumes_lots_fifo() -> None:
    store = Store(
        name="portfolio",
        balance=150.0,
        lots=[
            Lot(quantity=100.0, created_step=0, cost_basis=100.0),
            Lot(quantity=50.0, created_step=1, cost_basis=50.0),
        ],
    )

    consumed = store.withdraw_amount(120.0)

    assert store.balance == 30.0
    assert [lot.quantity for lot in store.lots] == [30.0]
    assert [lot.quantity for lot in consumed] == [100.0, 20.0]


def test_withdraw_amount_splits_metadata_proportionally() -> None:
    store = Store(
        name="portfolio",
        balance=100.0,
        lots=[
            Lot(
                quantity=100.0,
                created_step=0,
                cost_basis=50.0,
                metadata={"vorabpauschale_taxed": 10.0},
            )
        ],
    )

    consumed = store.withdraw_amount(40.0)

    # 40% of the lot is withdrawn, so 40% of every metadata value goes with it.
    assert pytest.approx(consumed[0].metadata["vorabpauschale_taxed"]) == 4.0
    assert pytest.approx(consumed[0].cost_basis) == 20.0
    assert pytest.approx(store.lots[0].metadata["vorabpauschale_taxed"]) == 6.0
    assert pytest.approx(store.lots[0].cost_basis) == 30.0
    assert pytest.approx(store.lots[0].quantity) == 60.0


def test_withdraw_amount_without_lots_uses_plain_balance() -> None:
    store = Store(name="cash", balance=100.0)
    consumed = store.withdraw_amount(30.0)

    assert store.balance == 70.0
    assert consumed == []


def test_apply_percentage_growth_scales_balance_and_lots() -> None:
    store = Store(
        name="portfolio",
        balance=150.0,
        lots=[
            Lot(quantity=100.0, created_step=0, cost_basis=100.0),
            Lot(quantity=50.0, created_step=1, cost_basis=50.0),
        ],
    )

    store.apply_percentage_growth(0.10)

    assert pytest.approx(store.balance) == 165.0
    assert pytest.approx(store.lots[0].quantity) == 110.0
    assert pytest.approx(store.lots[1].quantity) == 55.0
