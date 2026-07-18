"""Loan amortization - see Docs/06-Feature-Berechnungen.md."""

from pydantic import BaseModel


class AmortizationRow(BaseModel):
    """One period of a loan amortization schedule."""

    period: int
    payment: float
    interest: float
    principal: float
    remaining_balance: float


def loan_monthly_payment(principal: float, monthly_rate: float, term_months: int) -> float:
    """Fixed periodic payment that fully amortizes principal over
    term_months at monthly_rate per period."""
    _validate_rate(monthly_rate)
    _validate_term(term_months)
    if monthly_rate == 0:
        return principal / term_months
    growth_factor = (1 + monthly_rate) ** term_months
    return principal * monthly_rate * growth_factor / (growth_factor - 1)


def loan_total_interest(principal: float, monthly_rate: float, term_months: int) -> float:
    """Total interest paid over the full term of a fixed-payment loan."""
    payment = loan_monthly_payment(principal, monthly_rate, term_months)
    return payment * term_months - principal


def loan_remaining_balance(
    principal: float, monthly_rate: float, term_months: int, payments_made: int
) -> float:
    """Outstanding balance of a fixed-payment loan after payments_made
    payments."""
    _validate_rate(monthly_rate)
    _validate_term(term_months)
    if payments_made < 0 or payments_made > term_months:
        msg = f"payments_made must be between 0 and {term_months}, got {payments_made}"
        raise ValueError(msg)
    if monthly_rate == 0:
        payment = principal / term_months
        return principal - payment * payments_made
    payment = loan_monthly_payment(principal, monthly_rate, term_months)
    growth_factor = (1 + monthly_rate) ** payments_made
    return principal * growth_factor - payment * (growth_factor - 1) / monthly_rate


def loan_amortization_schedule(
    principal: float, monthly_rate: float, term_months: int
) -> list[AmortizationRow]:
    """Full period-by-period breakdown of a fixed-payment loan into
    interest and principal."""
    _validate_rate(monthly_rate)
    _validate_term(term_months)
    payment = loan_monthly_payment(principal, monthly_rate, term_months)
    balance = principal
    rows: list[AmortizationRow] = []
    for period in range(1, term_months + 1):
        interest = balance * monthly_rate
        principal_paid = payment - interest
        balance -= principal_paid
        remaining = 0.0 if period == term_months else balance
        rows.append(
            AmortizationRow(
                period=period,
                payment=round(payment, 2),
                interest=round(interest, 2),
                principal=round(principal_paid, 2),
                remaining_balance=round(remaining, 2),
            )
        )
    return rows


def _validate_rate(rate: float) -> None:
    if rate <= -1:
        msg = f"rate must be > -1 (a loss of 100% or more), got {rate}"
        raise ValueError(msg)


def _validate_term(term_months: int) -> None:
    if term_months <= 0:
        msg = f"term_months must be > 0, got {term_months}"
        raise ValueError(msg)
