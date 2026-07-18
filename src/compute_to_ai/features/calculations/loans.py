"""Loan amortization - see Docs/06-Feature-Berechnungen.md."""

from pydantic import BaseModel


class AmortizationRow(BaseModel):
    """One period of a loan amortization schedule."""

    period: int
    payment: float
    interest: float
    principal: float
    remaining_balance: float


class ExtraPayment(BaseModel):
    """A one-time extra payment applied on top of the regular payment in
    a given period."""

    period: int
    amount: float


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


def loan_amortization_schedule_with_extra_payments(
    principal: float,
    monthly_rate: float,
    term_months: int,
    extra_payments: list[ExtraPayment],
) -> list[AmortizationRow]:
    """Period-by-period breakdown of a fixed-payment loan where one or
    more extra_payments are applied on top of the regular payment. The
    regular payment stays at its original amount and extra payments
    shorten the remaining term instead (the common German
    "Sondertilgung" convention: Rate bleibt gleich, Restlaufzeit
    verkürzt sich), so the returned schedule is typically shorter than
    term_months."""
    _validate_rate(monthly_rate)
    _validate_term(term_months)
    for extra in extra_payments:
        if not 1 <= extra.period <= term_months:
            msg = f"extra payment period {extra.period} must be between 1 and {term_months}"
            raise ValueError(msg)

    extra_by_period = {extra.period: extra.amount for extra in extra_payments}
    payment = loan_monthly_payment(principal, monthly_rate, term_months)
    balance = principal
    rows: list[AmortizationRow] = []
    period = 0
    while balance > 0.01 and period < term_months:
        period += 1
        interest = balance * monthly_rate
        scheduled_principal = payment - interest
        principal_paid = min(scheduled_principal + extra_by_period.get(period, 0.0), balance)
        balance -= principal_paid
        rows.append(
            AmortizationRow(
                period=period,
                payment=round(principal_paid + interest, 2),
                interest=round(interest, 2),
                principal=round(principal_paid, 2),
                remaining_balance=round(max(balance, 0.0), 2),
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
