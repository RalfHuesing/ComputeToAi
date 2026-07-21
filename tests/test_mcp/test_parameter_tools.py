"""Unit tests for finance_set_plan_parameter and finance_get_plan_parameters MCP tools."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.timeline import Timeline
from compute_to_ai.mcp.tools.finance import register_finance_tools
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan


def test_mcp_parameter_tools(tmp_path: Path) -> None:
    """Test setting and retrieving plan parameters via registered MCP tools."""
    # Create test plan
    plan = Plan(name="mcp_param_plan", timeline=Timeline(step_count=10))
    save_plan(tmp_path, plan)

    mcp = FastMCP("test_server")
    register_finance_tools(mcp, tmp_path)

    # FastMCP tools can be called via their inner python function
    set_tool = mcp._tool_manager._tools["finance_set_plan_parameter"].fn
    get_tool = mcp._tool_manager._tools["finance_get_plan_parameters"].fn

    # 1. Initially parameters dict is empty
    params = get_tool("mcp_param_plan")
    assert params == {}

    # 2. Set parameter
    res = set_tool("mcp_param_plan", key="inflation_general", value=0.025)
    assert "inflation_general" in res
    assert "0.025" in res

    # 3. Retrieve parameters again
    params_after = get_tool("mcp_param_plan")
    assert params_after == {"inflation_general": 0.025}

    # 4. Verify parameter persisted on Plan object
    reloaded_plan = load_plan(tmp_path, "mcp_param_plan")
    assert reloaded_plan.parameters == {"inflation_general": 0.025}
