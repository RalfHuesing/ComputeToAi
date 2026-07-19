from datetime import date

import pytest

from compute_to_ai.features.calculations.holdings import (
    ShareTransaction,
    market_value,
    shares_from_transactions,
)


def test_shares_from_transactions_sums_pure_buys() -> None:
    transactions = [
        ShareTransaction(date=date(2020, 1, 1), shares=10.0),
        ShareTransaction(date=date(2021, 1, 1), shares=5.0),
    ]

    assert shares_from_transactions(transactions) == pytest.approx(15.0)


def test_shares_from_transactions_nets_a_buy_and_partial_sell() -> None:
    transactions = [
        ShareTransaction(date=date(2020, 1, 1), shares=10.0),
        ShareTransaction(date=date(2021, 1, 1), shares=-4.0),
    ]

    assert shares_from_transactions(transactions) == pytest.approx(6.0)


def test_shares_from_transactions_of_empty_list_is_zero() -> None:
    assert shares_from_transactions([]) == pytest.approx(0.0)


def test_market_value_multiplies_shares_by_price() -> None:
    assert market_value(shares=10.0, price=119.49) == pytest.approx(1194.9)
