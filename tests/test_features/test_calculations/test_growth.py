import pytest

from compute_to_ai.features.calculations.growth import (
    future_value_lump_sum,
    future_value_series,
    present_value_annuity,
    present_value_lump_sum,
)


def test_future_value_lump_sum_doubles_at_100_percent() -> None:
    assert future_value_lump_sum(100.0, 1.0, 1) == 200.0


def test_present_value_lump_sum_is_the_inverse_of_future_value() -> None:
    assert present_value_lump_sum(200.0, 1.0, 1) == 100.0


def test_future_value_lump_sum_rejects_years_below_zero() -> None:
    with pytest.raises(ValueError, match="years"):
        future_value_lump_sum(100.0, 0.05, -1)


def test_future_value_lump_sum_rejects_rate_at_or_below_negative_one() -> None:
    with pytest.raises(ValueError, match="rate"):
        future_value_lump_sum(100.0, -1.0, 1)


def test_future_value_series_at_zero_rate_is_a_plain_sum() -> None:
    """100 €/month, 0 % return, 480 months -> 48,000 € (matches the
    Milestone-1-era engine golden case, computed here via the closed-form
    annuity formula instead of a step-by-step simulation)."""
    assert future_value_series(100.0, 0.0, 480) == 48_000.0


def test_future_value_series_matches_known_reference_value() -> None:
    """100/period at 1%/period for 12 periods -> 1,268.25 (standard
    future-value-of-an-ordinary-annuity reference figure)."""
    result = future_value_series(100.0, 0.01, 12)

    assert result == pytest.approx(1268.25, abs=0.01)


def test_present_value_annuity_at_zero_rate_is_a_plain_sum() -> None:
    assert present_value_annuity(100.0, 0.0, 10) == 1000.0


def test_present_value_annuity_matches_known_reference_value() -> None:
    """100/year for 10 years at 5% -> 772.17 (standard annuity
    present-value reference figure, Rentenbarwert)."""
    result = present_value_annuity(100.0, 0.05, 10)

    assert result == pytest.approx(772.17, abs=0.01)
