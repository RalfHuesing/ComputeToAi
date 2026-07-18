import pytest

from compute_to_ai.features.calculations.growth import (
    adjust_for_inflation,
    cagr,
    future_value_lump_sum,
    future_value_series,
    periods_to_reach_future_value,
    periods_until_depletion,
    present_value_annuity,
    present_value_lump_sum,
    real_rate_of_return,
    required_payment_for_future_value,
    sustainable_withdrawal_for_depletion,
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


def test_cagr_of_a_value_that_doubles_every_year_is_100_percent() -> None:
    """100 -> 800 over 3 years is exactly a doubling each year (2^3 = 8)."""
    assert cagr(100.0, 800.0, 3) == pytest.approx(1.0)


def test_cagr_rejects_non_positive_values() -> None:
    with pytest.raises(ValueError, match="begin_value"):
        cagr(0.0, 100.0, 1)


def test_real_rate_of_return_is_zero_when_nominal_equals_inflation() -> None:
    assert real_rate_of_return(1.0, 1.0) == pytest.approx(0.0)


def test_real_rate_of_return_equals_nominal_when_inflation_is_zero() -> None:
    assert real_rate_of_return(0.1, 0.0) == pytest.approx(0.1)


def test_adjust_for_inflation_matches_present_value_lump_sum() -> None:
    """100 % inflation over 1 year halves purchasing power, same math as
    discounting an investment return."""
    assert adjust_for_inflation(220.0, 1.0, 1) == present_value_lump_sum(220.0, 1.0, 1)


def test_future_value_series_at_zero_rate_is_a_plain_sum() -> None:
    """100 €/month, 0 % return, 480 months -> 48,000 €, computed here via
    the closed-form annuity formula instead of a step-by-step simulation
    (see tests/test_engine/test_simulation.py for the simulated version)."""
    assert future_value_series(100.0, 0.0, 480) == 48_000.0


def test_future_value_series_matches_known_reference_value() -> None:
    """100/period at 1%/period for 12 periods -> 1,268.25 (standard
    future-value-of-an-ordinary-annuity reference figure)."""
    result = future_value_series(100.0, 0.01, 12)

    assert result == pytest.approx(1268.25, abs=0.01)


def test_required_payment_for_future_value_at_zero_rate() -> None:
    assert required_payment_for_future_value(48_000.0, 0.0, 480) == 100.0


def test_required_payment_for_future_value_is_the_inverse_of_future_value_series() -> None:
    payment = required_payment_for_future_value(1268.25, 0.01, 12)

    assert payment == pytest.approx(100.0, abs=0.01)


def test_periods_to_reach_future_value_at_zero_rate() -> None:
    assert periods_to_reach_future_value(100.0, 0.0, 48_000.0) == 480.0


def test_periods_to_reach_future_value_is_the_inverse_of_future_value_series() -> None:
    periods = periods_to_reach_future_value(100.0, 0.01, 1268.25)

    assert periods == pytest.approx(12.0, abs=0.01)


def test_present_value_annuity_at_zero_rate_is_a_plain_sum() -> None:
    assert present_value_annuity(100.0, 0.0, 10) == 1000.0


def test_present_value_annuity_matches_known_reference_value() -> None:
    """100/year for 10 years at 5% -> 772.17 (standard annuity
    present-value reference figure, Rentenbarwert)."""
    result = present_value_annuity(100.0, 0.05, 10)

    assert result == pytest.approx(772.17, abs=0.01)


def test_sustainable_withdrawal_for_depletion_at_zero_rate() -> None:
    assert sustainable_withdrawal_for_depletion(12_000.0, 0.0, 12) == 1000.0


def test_sustainable_withdrawal_is_the_inverse_of_present_value_annuity() -> None:
    capital = present_value_annuity(100.0, 0.05, 10)

    withdrawal = sustainable_withdrawal_for_depletion(capital, 0.05, 10)

    assert withdrawal == pytest.approx(100.0)


def test_periods_until_depletion_at_zero_rate() -> None:
    assert periods_until_depletion(12_000.0, 0.0, 1000.0) == 12.0


def test_periods_until_depletion_is_the_inverse_of_present_value_annuity() -> None:
    capital = present_value_annuity(100.0, 0.05, 10)

    periods = periods_until_depletion(capital, 0.05, 100.0)

    assert periods == pytest.approx(10.0, abs=1e-6)


def test_periods_until_depletion_rejects_a_withdrawal_that_never_depletes_capital() -> None:
    """1,000 capital at 10 % grows 100/period; withdrawing only 50/period
    never catches up."""
    with pytest.raises(ValueError, match="never depletes"):
        periods_until_depletion(1000.0, 0.10, 50.0)
