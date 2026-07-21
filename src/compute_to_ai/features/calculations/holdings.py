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


class ContributionBucket(BaseModel):
    """One target of a new contribution: its current value and target weight
    within the group being allocated across (see `contribution_allocation`)."""

    name: str
    current_value: float
    target_weight: float


def contribution_allocation(
    buckets: list[ContributionBucket], new_amount: float
) -> dict[str, float]:
    """Distribute `new_amount` across `buckets` to move the combined result as
    close as possible to each bucket's target weight, without ever suggesting
    to sell/reduce an existing bucket - this only ever allocates newly
    incoming money, it can't undo an already-overweight bucket.

    1. `new_total` = every bucket's current value, plus `new_amount`.
    2. Each bucket's gap is `max(0, target_weight * new_total - current_value)`
       - a bucket already at or above its target has a gap of exactly 0 and
       gets nothing this round; its excess is never reduced.
    3. If any bucket has a positive gap, `new_amount` is allocated
       proportionally to each bucket's gap.
    4. If every gap is 0 (can happen if `target_weight`s don't sum to 1, or
       every bucket is simultaneously overweight), falls back to allocating
       `new_amount` purely by `target_weight` (normalized to sum to 1 first
       if needed).

    Whichever branch runs, the returned dict's values sum to `new_amount`
    (up to floating point tolerance) and use every bucket's `name` as key,
    including buckets that get 0.0.
    """
    if not buckets:
        msg = "buckets must not be empty"
        raise ValueError(msg)
    if new_amount < 0.0:
        msg = f"new_amount must be >= 0, got {new_amount!r}"
        raise ValueError(msg)
    for bucket in buckets:
        if bucket.current_value < 0.0:
            msg = f"current_value must be >= 0, got {bucket.current_value!r} for {bucket.name!r}"
            raise ValueError(msg)
        if bucket.target_weight < 0.0:
            msg = f"target_weight must be >= 0, got {bucket.target_weight!r} for {bucket.name!r}"
            raise ValueError(msg)

    new_total = sum(bucket.current_value for bucket in buckets) + new_amount
    gaps = {
        bucket.name: max(0.0, bucket.target_weight * new_total - bucket.current_value)
        for bucket in buckets
    }
    total_gap = sum(gaps.values())

    if total_gap > 0.0:
        return {name: new_amount * gap / total_gap for name, gap in gaps.items()}

    total_weight = sum(bucket.target_weight for bucket in buckets)
    if total_weight > 0.0:
        return {bucket.name: new_amount * bucket.target_weight / total_weight for bucket in buckets}
    equal_share = new_amount / len(buckets)
    return {bucket.name: equal_share for bucket in buckets}
