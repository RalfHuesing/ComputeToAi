"""Finance MCP tools domain sub-package."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.mcp.tools.finance._cashflow import register_cashflow_tools
from compute_to_ai.mcp.tools.finance._contribution import register_contribution_tools
from compute_to_ai.mcp.tools.finance._goal_mc import register_goal_and_monte_carlo_tools
from compute_to_ai.mcp.tools.finance._liability import register_liability_tools
from compute_to_ai.mcp.tools.finance._live_price import register_live_price_tools
from compute_to_ai.mcp.tools.finance._parameter import register_parameter_tools
from compute_to_ai.mcp.tools.finance._path_audit import register_path_audit_tools
from compute_to_ai.mcp.tools.finance._phase import register_phase_tools
from compute_to_ai.mcp.tools.finance._portfolio import register_portfolio_tools
from compute_to_ai.mcp.tools.finance._position import register_position_tools
from compute_to_ai.mcp.tools.finance._reports import register_report_tools
from compute_to_ai.mcp.tools.finance._tax_pension import register_tax_and_pension_tools


def register_finance_tools(mcp: FastMCP, working_directory: Path) -> None:
    """Register all finance building-block, goal-condition, and Monte-Carlo tools."""
    register_live_price_tools(mcp, working_directory)
    register_position_tools(mcp, working_directory)
    register_phase_tools(mcp, working_directory)
    register_cashflow_tools(mcp, working_directory)
    register_liability_tools(mcp, working_directory)
    register_portfolio_tools(mcp, working_directory)
    register_contribution_tools(mcp, working_directory)
    register_tax_and_pension_tools(mcp, working_directory)
    register_goal_and_monte_carlo_tools(mcp, working_directory)
    register_path_audit_tools(mcp, working_directory)
    register_report_tools(mcp, working_directory)
    register_parameter_tools(mcp, working_directory)
