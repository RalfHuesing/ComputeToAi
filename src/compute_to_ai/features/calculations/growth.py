"""Compound growth and discounting - see Docs/06-Feature-Berechnungen.md."""

import math


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


def cagr(begin_value: float, end_value: float, years: float) -> float:
    """Compound annual growth rate implied by begin_value growing to
    end_value over years (the inverse of future_value_lump_sum, solved
    for the rate)."""
    _validate_positive(begin_value, "begin_value")
    _validate_positive(end_value, "end_value")
    _validate_positive(years, "years")
    return (end_value / begin_value) ** (1 / years) - 1


def real_rate_of_return(nominal_rate: float, inflation_rate: float) -> float:
    """Inflation-adjusted rate of return (Fisher equation)."""
    _validate_rate(nominal_rate)
    _validate_rate(inflation_rate)
    return (1 + nominal_rate) / (1 + inflation_rate) - 1


def adjust_for_inflation(nominal_amount: float, inflation_rate: float, years: float) -> float:
    """Purchasing power of a future nominal amount in today's money."""
    return present_value_lump_sum(nominal_amount, inflation_rate, years)


def net_real_return(
    nominal_return: float,
    inflation_rate: float,
    tax_rate: float,
    partial_exemption_rate: float = 0.0,
) -> float:
    """Real rate of return after tax on the gain and inflation.

    tax_rate and partial_exemption_rate are plain parameters, not built-in
    German tax constants (German tax law belongs to Feature Finanzen, not
    here - see Docs/06-Feature-Berechnungen.md); a caller wanting German
    Abgeltungsteuer numbers supplies its rate explicitly. This treats the
    full nominal gain as taxed in the year it accrues, which approximates
    but doesn't replace the Vorabpauschale/realization-timing rules Feature
    Finanzen's tax building block models precisely.
    """
    _validate_rate(nominal_return)
    _validate_rate(inflation_rate)
    if not 0.0 <= tax_rate <= 1.0:
        msg = f"tax_rate must be within [0, 1], got {tax_rate}"
        raise ValueError(msg)
    if not 0.0 <= partial_exemption_rate <= 1.0:
        msg = f"partial_exemption_rate must be within [0, 1], got {partial_exemption_rate}"
        raise ValueError(msg)
    effective_tax_rate = tax_rate * (1.0 - partial_exemption_rate)
    net_nominal_return = nominal_return * (1.0 - effective_tax_rate)
    return real_rate_of_return(net_nominal_return, inflation_rate)


def future_value_series(payment_per_period: float, periodic_rate: float, periods: int) -> float:
    """Future value of equal contributions made at the end of each period
    (ordinary annuity), e.g. monthly savings compounding monthly."""
    _validate_rate(periodic_rate)
    _validate_non_negative(periods, "periods")
    if periodic_rate == 0:
        return payment_per_period * periods
    growth_factor = (1 + periodic_rate) ** periods
    return payment_per_period * (growth_factor - 1) / periodic_rate


def required_payment_for_future_value(
    target_future_value: float, periodic_rate: float, periods: int
) -> float:
    """Periodic contribution needed to reach target_future_value (the
    inverse of future_value_series, solved for the payment)."""
    _validate_rate(periodic_rate)
    _validate_positive(periods, "periods")
    if periodic_rate == 0:
        return target_future_value / periods
    growth_factor = (1 + periodic_rate) ** periods
    return target_future_value * periodic_rate / (growth_factor - 1)


def periods_to_reach_future_value(
    payment_per_period: float, periodic_rate: float, target_future_value: float
) -> float:
    """Number of periods of payment_per_period needed to reach
    target_future_value (the inverse of future_value_series, solved for
    the period count)."""
    _validate_rate(periodic_rate)
    _validate_positive(payment_per_period, "payment_per_period")
    if periodic_rate == 0:
        return target_future_value / payment_per_period
    log_argument = 1 + (target_future_value * periodic_rate) / payment_per_period
    if log_argument <= 0:
        msg = (
            "target_future_value is not reachable with a positive "
            "payment_per_period at this periodic_rate"
        )
        raise ValueError(msg)
    return math.log(log_argument) / math.log(1 + periodic_rate)


def present_value_annuity(payment_per_period: float, periodic_rate: float, periods: int) -> float:
    """Present value of equal payments received at the end of each period
    for `periods` periods, discounted at periodic_rate (Rentenbarwert)."""
    _validate_rate(periodic_rate)
    _validate_non_negative(periods, "periods")
    if periodic_rate == 0:
        return payment_per_period * periods
    discount_factor = 1 - (1 + periodic_rate) ** -periods
    return payment_per_period * discount_factor / periodic_rate


def sustainable_withdrawal_for_depletion(
    available_capital: float, periodic_rate: float, periods: int
) -> float:
    """Constant periodic withdrawal that exactly depletes available_capital
    over `periods` periods (the inverse of present_value_annuity, solved
    for the payment - the same formula as a loan payment, framed for
    retirement drawdown instead of loan payoff)."""
    _validate_rate(periodic_rate)
    _validate_positive(periods, "periods")
    if periodic_rate == 0:
        return available_capital / periods
    growth_factor = (1 + periodic_rate) ** periods
    return available_capital * periodic_rate * growth_factor / (growth_factor - 1)


def periods_until_depletion(
    available_capital: float, periodic_rate: float, withdrawal_per_period: float
) -> float:
    """Number of periods until available_capital is fully depleted by
    withdrawing withdrawal_per_period at the end of each period (the
    inverse of present_value_annuity, solved for the period count)."""
    _validate_rate(periodic_rate)
    _validate_positive(withdrawal_per_period, "withdrawal_per_period")
    if periodic_rate == 0:
        return available_capital / withdrawal_per_period
    remaining_share = 1 - available_capital * periodic_rate / withdrawal_per_period
    if remaining_share <= 0:
        msg = (
            "withdrawal_per_period does not exceed the capital's periodic "
            "growth, so available_capital never depletes"
        )
        raise ValueError(msg)
    return -math.log(remaining_share) / math.log(1 + periodic_rate)


def inflation_adjusted_withdrawal_for_depletion(
    available_capital: float, nominal_rate: float, inflation_rate: float, periods: int
) -> float:
    """Starting withdrawal that exactly depletes available_capital over
    `periods` periods when the withdrawal itself grows by inflation_rate
    every subsequent period, keeping it level in real (purchasing-power)
    terms - the inflation-indexed sibling of
    sustainable_withdrawal_for_depletion, which assumes a flat, non-
    growing withdrawal instead."""
    _validate_rate(nominal_rate)
    _validate_rate(inflation_rate)
    _validate_positive(periods, "periods")
    if nominal_rate == inflation_rate:
        return available_capital / periods
    real_growth_ratio = (1 + inflation_rate) / (1 + nominal_rate)
    return available_capital * (nominal_rate - inflation_rate) / (1 - real_growth_ratio**periods)


def _validate_rate(rate: float) -> None:
    if rate <= -1:
        msg = f"rate must be > -1 (a loss of 100% or more), got {rate}"
        raise ValueError(msg)


def _validate_non_negative(value: float, name: str) -> None:
    if value < 0:
        msg = f"{name} must be >= 0, got {value}"
        raise ValueError(msg)


def _validate_positive(value: float, name: str) -> None:
    if value <= 0:
        msg = f"{name} must be > 0, got {value}"
        raise ValueError(msg)
