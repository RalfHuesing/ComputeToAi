"""Finance MCP tools domain sub-package."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.mcp.tools.finance._cashflow import _register_cashflow_tools
from compute_to_ai.mcp.tools.finance._contribution import _register_contribution_tools
from compute_to_ai.mcp.tools.finance._goal_mc import _register_goal_and_monte_carlo_tools
from compute_to_ai.mcp.tools.finance._liability import _register_liability_tools
from compute_to_ai.mcp.tools.finance._live_price import _register_live_price_tools
from compute_to_ai.mcp.tools.finance._parameter import _register_parameter_tools
from compute_to_ai.mcp.tools.finance._path_audit import _register_path_audit_tools
from compute_to_ai.mcp.tools.finance._phase import _register_phase_tools
from compute_to_ai.mcp.tools.finance._portfolio import _register_portfolio_tools
from compute_to_ai.mcp.tools.finance._position import _register_position_tools
from compute_to_ai.mcp.tools.finance._reports import _register_report_tools
from compute_to_ai.mcp.tools.finance._tax_pension import _register_tax_and_pension_tools


def register_finance_tools(mcp: FastMCP, working_directory: Path) -> None:
    """Register all finance building-block, goal-condition, and Monte-Carlo tools."""
    _register_live_price_tools(mcp, working_directory)
    _register_position_tools(mcp, working_directory)
    _register_phase_tools(mcp, working_directory)
    _register_cashflow_tools(mcp, working_directory)
    _register_liability_tools(mcp, working_directory)
    _register_portfolio_tools(mcp, working_directory)
    _register_contribution_tools(mcp, working_directory)
    _register_tax_and_pension_tools(mcp, working_directory)
    _register_goal_and_monte_carlo_tools(mcp, working_directory)
    _register_path_audit_tools(mcp, working_directory)
    _register_report_tools(mcp, working_directory)
    _register_parameter_tools(mcp, working_directory)
