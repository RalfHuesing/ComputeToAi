"""Cash-flow analysis requiring numerical root-finding, not a closed-form
formula - see Docs/06-Feature-Berechnungen.md.
"""

from collections.abc import Callable
from datetime import date

from pydantic import BaseModel

from compute_to_ai.features.calculations.growth import present_value_annuity
from compute_to_ai.features.calculations.loans import loan_monthly_payment


class CashFlow(BaseModel):
    """A single dated cash flow: positive = money received, negative =
    money paid out."""

    date: date
    amount: float


def xirr(cash_flows: list[CashFlow]) -> float:
    """Annualized internal rate of return for irregularly dated, unequal
    cash flows - the rate at which their net present value is zero.
    There's no closed-form solution for an arbitrary cash-flow shape, so
    this is found by bisection."""
    if len(cash_flows) < 2:
        msg = "xirr needs at least two cash flows"
        raise ValueError(msg)
    if not any(cf.amount < 0 for cf in cash_flows) or not any(cf.amount > 0 for cf in cash_flows):
        msg = "xirr needs at least one negative and one positive cash flow"
        raise ValueError(msg)

    reference_date = cash_flows[0].date

    def npv_at_rate(rate: float) -> float:
        return sum(
            cf.amount / (1 + rate) ** ((cf.date - reference_date).days / 365.0) for cf in cash_flows
        )

    return _solve_annual_rate(npv_at_rate)


def effective_annual_rate(
    principal: float,
    nominal_annual_rate: float,
    term_months: int,
    upfront_fees: float = 0.0,
    disbursement_rate: float = 1.0,
) -> float:
    """Simplified effective annual rate of a fixed-payment loan once
    upfront fees and/or a reduced disbursement (Disagio) are accounted
    for: the rate at which the net amount actually disbursed equals the
    present value of the unchanged repayment schedule.

    This is a simplified model covering the common upfront-fee/
    disbursement-rate case, not a legally certified PAngV
    implementation - useful to sanity-check a loan offer, not a
    substitute for the lender's own disclosure.
    """
    if not 0 < disbursement_rate <= 1:
        msg = f"disbursement_rate must be in (0, 1], got {disbursement_rate}"
        raise ValueError(msg)
    net_disbursement = principal * disbursement_rate - upfront_fees
    if net_disbursement <= 0:
        msg = "net_disbursement (principal * disbursement_rate - upfront_fees) must be > 0"
        raise ValueError(msg)

    payment = loan_monthly_payment(principal, nominal_annual_rate / 12, term_months)

    def npv_at_rate(annual_rate: float) -> float:
        return net_disbursement - present_value_annuity(payment, annual_rate / 12, term_months)

    return _solve_annual_rate(npv_at_rate)


def _solve_annual_rate(npv_at_rate: Callable[[float], float]) -> float:
    """Bisection root-find for the annual rate where npv_at_rate(rate)
    crosses zero, searched over -99% to +1000% (a bracket wide enough
    for any realistic loan or investment cash flow)."""
    low, high = -0.99, 10.0
    npv_low, npv_high = npv_at_rate(low), npv_at_rate(high)
    if npv_low * npv_high > 0:
        msg = (
            "no rate between -99% and 1000% zeroes the net present value; "
            "check that the cash flows contain both an outflow and an inflow"
        )
        raise ValueError(msg)

    for _ in range(100):
        mid = (low + high) / 2
        npv_mid = npv_at_rate(mid)
        if abs(npv_mid) < 1e-9:
            return mid
        if npv_low * npv_mid < 0:
            high = mid
        else:
            low, npv_low = mid, npv_mid
    return (low + high) / 2
