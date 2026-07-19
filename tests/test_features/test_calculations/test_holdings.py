from datetime import date

import pytest

from compute_to_ai.features.calculations.holdings import (
    ContributionBucket,
    ShareTransaction,
    contribution_allocation,
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


def test_contribution_allocation_splits_proportionally_to_gaps_when_all_below_target() -> None:
    buckets = [
        ContributionBucket(name="a", current_value=100.0, target_weight=0.5),
        ContributionBucket(name="b", current_value=100.0, target_weight=0.3),
        ContributionBucket(name="c", current_value=100.0, target_weight=0.2),
    ]

    result = contribution_allocation(buckets, new_amount=300.0)

    assert result == pytest.approx({"a": 200.0, "b": 80.0, "c": 20.0})
    assert sum(result.values()) == pytest.approx(300.0)


def test_contribution_allocation_gives_overweight_bucket_nothing() -> None:
    buckets = [
        ContributionBucket(name="a", current_value=500.0, target_weight=0.5),
        ContributionBucket(name="b", current_value=100.0, target_weight=0.3),
        ContributionBucket(name="c", current_value=100.0, target_weight=0.2),
    ]

    result = contribution_allocation(buckets, new_amount=200.0)

    assert result["a"] == pytest.approx(0.0)
    assert result == pytest.approx({"a": 0.0, "b": 136.0, "c": 64.0})
    assert sum(result.values()) == pytest.approx(200.0)


def test_contribution_allocation_falls_back_to_weights_when_all_at_or_above_target() -> None:
    buckets = [
        ContributionBucket(name="a", current_value=1000.0, target_weight=0.2),
        ContributionBucket(name="b", current_value=1000.0, target_weight=0.1),
    ]

    result = contribution_allocation(buckets, new_amount=100.0)

    assert result == pytest.approx({"a": 200.0 / 3.0, "b": 100.0 / 3.0})
    assert sum(result.values()) == pytest.approx(100.0)


def test_contribution_allocation_includes_zero_bucket_and_sums_to_new_amount() -> None:
    buckets = [
        ContributionBucket(name="a", current_value=500.0, target_weight=0.5),
        ContributionBucket(name="b", current_value=100.0, target_weight=0.3),
        ContributionBucket(name="c", current_value=100.0, target_weight=0.2),
    ]

    result = contribution_allocation(buckets, new_amount=200.0)

    assert set(result.keys()) == {"a", "b", "c"}
    assert "a" in result
    assert result["a"] == pytest.approx(0.0)
    assert sum(result.values()) == pytest.approx(200.0)


def test_contribution_allocation_rejects_empty_buckets() -> None:
    with pytest.raises(ValueError, match="buckets"):
        contribution_allocation([], new_amount=100.0)


def test_contribution_allocation_rejects_negative_new_amount() -> None:
    buckets = [ContributionBucket(name="a", current_value=100.0, target_weight=1.0)]
    with pytest.raises(ValueError, match="new_amount"):
        contribution_allocation(buckets, new_amount=-1.0)


def test_contribution_allocation_rejects_negative_current_value() -> None:
    buckets = [ContributionBucket(name="a", current_value=-1.0, target_weight=1.0)]
    with pytest.raises(ValueError, match="current_value"):
        contribution_allocation(buckets, new_amount=100.0)


def test_contribution_allocation_rejects_negative_target_weight() -> None:
    buckets = [ContributionBucket(name="a", current_value=100.0, target_weight=-0.1)]
    with pytest.raises(ValueError, match="target_weight"):
        contribution_allocation(buckets, new_amount=100.0)
