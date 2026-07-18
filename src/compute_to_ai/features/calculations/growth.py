"""Compound growth and discounting - see Docs/06-Feature-Berechnungen.md."""


def future_value_lump_sum(principal: float, annual_rate: float, years: float) -> float:
    """Future value of a one-time investment under annual compounding."""
    _validate_rate(annual_rate)
    _validate_non_negative(years, "years")
    return principal * (1 + annual_rate) ** years


def present_value_lump_sum(future_amount: float, annual_rate: float, years: float) -> float:
    """Present value of a single future amount, discounted at annual_rate."""
    _validate_rate(annual_rate)
    _validate_non_negative(years, "years")
    return future_amount / (1 + annual_rate) ** years


def future_value_series(payment_per_period: float, periodic_rate: float, periods: int) -> float:
    """Future value of equal contributions made at the end of each period
    (ordinary annuity), e.g. monthly savings compounding monthly."""
    _validate_rate(periodic_rate)
    _validate_non_negative(periods, "periods")
    if periodic_rate == 0:
        return payment_per_period * periods
    growth_factor = (1 + periodic_rate) ** periods
    return payment_per_period * (growth_factor - 1) / periodic_rate


def present_value_annuity(payment_per_period: float, periodic_rate: float, periods: int) -> float:
    """Present value of equal payments received at the end of each period
    for `periods` periods, discounted at periodic_rate (Rentenbarwert)."""
    _validate_rate(periodic_rate)
    _validate_non_negative(periods, "periods")
    if periodic_rate == 0:
        return payment_per_period * periods
    discount_factor = 1 - (1 + periodic_rate) ** -periods
    return payment_per_period * discount_factor / periodic_rate


def _validate_rate(rate: float) -> None:
    if rate <= -1:
        msg = f"rate must be > -1 (a loss of 100% or more), got {rate}"
        raise ValueError(msg)


def _validate_non_negative(value: float, name: str) -> None:
    if value < 0:
        msg = f"{name} must be >= 0, got {value}"
        raise ValueError(msg)
