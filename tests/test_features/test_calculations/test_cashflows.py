from datetime import date

import pytest

from compute_to_ai.features.calculations.cashflows import CashFlow, effective_annual_rate, xirr


def test_xirr_of_a_simple_one_year_investment() -> None:
    """Invest 1,000 today, get back 1,200 exactly 365 days later -> 20%,
    matching Excel/Sheets' XIRR Actual/365 day-count convention."""
    cash_flows = [
        CashFlow(date=date(2025, 1, 1), amount=-1000.0),
        CashFlow(date=date(2026, 1, 1), amount=1200.0),
    ]

    assert xirr(cash_flows) == pytest.approx(0.2, abs=1e-6)


def test_xirr_rejects_fewer_than_two_cash_flows() -> None:
    with pytest.raises(ValueError, match="at least two"):
        xirr([CashFlow(date=date(2025, 1, 1), amount=-1000.0)])


def test_xirr_rejects_all_same_sign_cash_flows() -> None:
    cash_flows = [
        CashFlow(date=date(2025, 1, 1), amount=100.0),
        CashFlow(date=date(2026, 1, 1), amount=200.0),
    ]

    with pytest.raises(ValueError, match="negative and one positive"):
        xirr(cash_flows)


def test_effective_annual_rate_equals_nominal_rate_without_fees() -> None:
    """No fees, full disbursement -> the effective rate is just the
    nominal rate (sanity check against loan_monthly_payment/
    present_value_annuity being exact inverses)."""
    result = effective_annual_rate(10_000.0, 0.05, 60, upfront_fees=0.0, disbursement_rate=1.0)

    assert result == pytest.approx(0.05, abs=1e-6)


def test_effective_annual_rate_is_higher_with_upfront_fees() -> None:
    result = effective_annual_rate(10_000.0, 0.05, 60, upfront_fees=200.0, disbursement_rate=1.0)

    assert result > 0.05


def test_effective_annual_rate_rejects_out_of_range_disbursement_rate() -> None:
    with pytest.raises(ValueError, match="disbursement_rate"):
        effective_annual_rate(10_000.0, 0.05, 60, disbursement_rate=1.5)


def test_effective_annual_rate_rejects_fees_exceeding_principal() -> None:
    with pytest.raises(ValueError, match="net_disbursement"):
        effective_annual_rate(1000.0, 0.05, 12, upfront_fees=2000.0)
