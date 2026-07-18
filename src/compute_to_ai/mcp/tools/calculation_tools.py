"""Calculation tools: deterministic finance building blocks.

See Docs/06-Feature-Berechnungen.md for their purpose and
Docs/02-Architektur-und-MCP.md for the `calculations_` tool-name prefix.
Stateless, so unlike core_tools these are registered directly by
reference (no working_directory to inject via a closure).
"""

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.calculations.cashflows import effective_annual_rate, xirr
from compute_to_ai.features.calculations.dates import (
    age_in_years,
    age_to_step,
    step_to_age,
    years_between,
)
from compute_to_ai.features.calculations.growth import (
    adjust_for_inflation,
    cagr,
    future_value_lump_sum,
    future_value_series,
    inflation_adjusted_withdrawal_for_depletion,
    net_real_return,
    periods_to_reach_future_value,
    periods_until_depletion,
    present_value_annuity,
    present_value_lump_sum,
    real_rate_of_return,
    required_payment_for_future_value,
    sustainable_withdrawal_for_depletion,
)
from compute_to_ai.features.calculations.loans import (
    loan_amortization_schedule,
    loan_amortization_schedule_with_extra_payments,
    loan_monthly_payment,
    loan_remaining_balance,
    loan_total_interest,
)


def register_calculation_tools(mcp: FastMCP) -> None:
    """Register the deterministic calculation tools."""
    mcp.tool(name="calculations_years_between")(years_between)
    mcp.tool(name="calculations_age_in_years")(age_in_years)
    mcp.tool(name="calculations_step_to_age")(step_to_age)
    mcp.tool(name="calculations_age_to_step")(age_to_step)

    mcp.tool(name="calculations_future_value_lump_sum")(future_value_lump_sum)
    mcp.tool(name="calculations_present_value_lump_sum")(present_value_lump_sum)
    mcp.tool(name="calculations_cagr")(cagr)
    mcp.tool(name="calculations_real_rate_of_return")(real_rate_of_return)
    mcp.tool(name="calculations_net_real_return")(net_real_return)
    mcp.tool(name="calculations_adjust_for_inflation")(adjust_for_inflation)

    mcp.tool(name="calculations_future_value_series")(future_value_series)
    mcp.tool(name="calculations_required_payment_for_future_value")(
        required_payment_for_future_value
    )
    mcp.tool(name="calculations_periods_to_reach_future_value")(periods_to_reach_future_value)

    mcp.tool(name="calculations_present_value_annuity")(present_value_annuity)
    mcp.tool(name="calculations_sustainable_withdrawal_for_depletion")(
        sustainable_withdrawal_for_depletion
    )
    mcp.tool(name="calculations_periods_until_depletion")(periods_until_depletion)
    mcp.tool(name="calculations_inflation_adjusted_withdrawal_for_depletion")(
        inflation_adjusted_withdrawal_for_depletion
    )

    mcp.tool(name="calculations_loan_monthly_payment")(loan_monthly_payment)
    mcp.tool(name="calculations_loan_total_interest")(loan_total_interest)
    mcp.tool(name="calculations_loan_remaining_balance")(loan_remaining_balance)
    mcp.tool(name="calculations_loan_amortization_schedule")(loan_amortization_schedule)
    mcp.tool(name="calculations_loan_amortization_schedule_with_extra_payments")(
        loan_amortization_schedule_with_extra_payments
    )

    mcp.tool(name="calculations_xirr")(xirr)
    mcp.tool(name="calculations_effective_annual_rate")(effective_annual_rate)
