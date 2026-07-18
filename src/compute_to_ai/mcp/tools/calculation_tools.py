"""Calculation tools: deterministic finance building blocks.

See Docs/06-Feature-Berechnungen.md for their purpose and
Docs/02-Architektur-und-MCP.md for the `calculations_` tool-name prefix.
Stateless, so unlike core_tools these are registered directly by
reference (no working_directory to inject via a closure).
"""

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.calculations.dates import age_in_years, years_between
from compute_to_ai.features.calculations.growth import (
    future_value_lump_sum,
    future_value_series,
    present_value_annuity,
    present_value_lump_sum,
)
from compute_to_ai.features.calculations.loans import loan_monthly_payment, loan_total_interest


def register_calculation_tools(mcp: FastMCP) -> None:
    """Register the deterministic calculation tools."""
    mcp.tool(name="calculations_years_between")(years_between)
    mcp.tool(name="calculations_age_in_years")(age_in_years)
    mcp.tool(name="calculations_future_value_lump_sum")(future_value_lump_sum)
    mcp.tool(name="calculations_present_value_lump_sum")(present_value_lump_sum)
    mcp.tool(name="calculations_future_value_series")(future_value_series)
    mcp.tool(name="calculations_present_value_annuity")(present_value_annuity)
    mcp.tool(name="calculations_loan_monthly_payment")(loan_monthly_payment)
    mcp.tool(name="calculations_loan_total_interest")(loan_total_interest)
