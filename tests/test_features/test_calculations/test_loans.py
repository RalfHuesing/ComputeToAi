import pytest

from compute_to_ai.features.calculations.loans import loan_monthly_payment, loan_total_interest


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
