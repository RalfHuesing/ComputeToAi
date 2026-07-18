"""Loan amortization - see Docs/06-Feature-Berechnungen.md."""


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


def _validate_rate(rate: float) -> None:
    if rate <= -1:
        msg = f"rate must be > -1 (a loss of 100% or more), got {rate}"
        raise ValueError(msg)


def _validate_term(term_months: int) -> None:
    if term_months <= 0:
        msg = f"term_months must be > 0, got {term_months}"
        raise ValueError(msg)
