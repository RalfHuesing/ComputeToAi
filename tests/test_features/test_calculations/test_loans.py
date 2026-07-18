import pytest

from compute_to_ai.features.calculations.loans import (
    loan_amortization_schedule,
    loan_monthly_payment,
    loan_remaining_balance,
    loan_total_interest,
)


def test_loan_monthly_payment_at_zero_rate_is_a_plain_division() -> None:
    assert loan_monthly_payment(12_000.0, 0.0, 12) == 1000.0


def test_loan_monthly_payment_single_period_equals_principal_plus_interest() -> None:
    """Borrow 100 at 1% for a single period -> owe back exactly 101."""
    assert loan_monthly_payment(100.0, 0.01, 1) == pytest.approx(101.0)


def test_loan_total_interest_at_zero_rate_is_zero() -> None:
    assert loan_total_interest(12_000.0, 0.0, 12) == 0.0


def test_loan_total_interest_single_period() -> None:
    assert loan_total_interest(100.0, 0.01, 1) == pytest.approx(1.0)


def test_loan_monthly_payment_rejects_zero_term() -> None:
    with pytest.raises(ValueError, match="term_months"):
        loan_monthly_payment(1000.0, 0.01, 0)


def test_loan_monthly_payment_rejects_rate_at_or_below_negative_one() -> None:
    with pytest.raises(ValueError, match="rate"):
        loan_monthly_payment(1000.0, -1.0, 12)


def test_loan_remaining_balance_at_zero_rate_is_a_plain_subtraction() -> None:
    assert loan_remaining_balance(12_000.0, 0.0, 12, 6) == 6000.0


def test_loan_remaining_balance_with_no_payments_made_is_the_principal() -> None:
    assert loan_remaining_balance(100.0, 0.01, 1, 0) == pytest.approx(100.0)


def test_loan_remaining_balance_after_all_payments_is_zero() -> None:
    assert loan_remaining_balance(100.0, 0.01, 1, 1) == pytest.approx(0.0, abs=1e-9)


def test_loan_remaining_balance_rejects_payments_made_beyond_term() -> None:
    with pytest.raises(ValueError, match="payments_made"):
        loan_remaining_balance(1000.0, 0.01, 12, 13)


def test_loan_amortization_schedule_at_zero_rate() -> None:
    schedule = loan_amortization_schedule(12_000.0, 0.0, 12)

    assert len(schedule) == 12
    assert schedule[0].payment == 1000.0
    assert schedule[0].interest == 0.0
    assert schedule[0].principal == 1000.0
    assert schedule[0].remaining_balance == 11_000.0
    assert schedule[-1].remaining_balance == 0.0


def test_loan_amortization_schedule_single_period() -> None:
    schedule = loan_amortization_schedule(100.0, 0.01, 1)

    assert len(schedule) == 1
    row = schedule[0]
    assert row.period == 1
    assert row.payment == pytest.approx(101.0)
    assert row.interest == pytest.approx(1.0)
    assert row.principal == pytest.approx(100.0)
    assert row.remaining_balance == 0.0


def test_loan_amortization_schedule_matches_remaining_balance_formula() -> None:
    """The last row's remaining_balance must agree with the closed-form
    loan_remaining_balance for the same number of payments."""
    schedule = loan_amortization_schedule(10_000.0, 0.02, 24)

    for row in (schedule[5], schedule[-1]):
        expected = loan_remaining_balance(10_000.0, 0.02, 24, row.period)
        assert row.remaining_balance == pytest.approx(expected, abs=0.01)
