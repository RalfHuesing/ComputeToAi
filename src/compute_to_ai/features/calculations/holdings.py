"""Depot-Bestand & Rebalancing-Rechner: pure arithmetic over share counts and
market values, no Plan/tax/correlation awareness - see Docs/06-Feature-Berechnungen.md.
"""

from datetime import date

from pydantic import BaseModel


class ShareTransaction(BaseModel):
    """A single dated share transaction: positive = shares bought, negative =
    shares sold (same sign convention as `CashFlow.amount` in `cashflows.py`)."""

    date: date
    shares: float


def shares_from_transactions(transactions: list[ShareTransaction]) -> float:
    """Net current share count: sum of signed shares across the transaction history.

    Pure arithmetic - this only tells you how many shares are held today,
    not their value or cost basis (see `market_value` and
    `compute_to_ai.features.finance.position.apply_transaction_history` for
    those, which additionally need the price paid per transaction).
    """
    return sum(transaction.shares for transaction in transactions)


def market_value(shares: float, price: float) -> float:
    """Market value of a position: shares held times current price per share."""
    return shares * price
