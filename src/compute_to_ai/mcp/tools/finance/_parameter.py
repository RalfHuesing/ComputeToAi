"""Central plan parameter management MCP tools."""

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan

logger = logging.getLogger(__name__)


def register_parameter_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_set_plan_parameter(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        key: str,
        value: float,
    ) -> str:
        """Set a central plan parameter (e.g. inflation_general = 0.025)."""
        plan = load_plan(working_directory, plan_name)
        plan.set_parameter(key, value)
        save_plan(working_directory, plan)
        logger.info(
            "finance_set_plan_parameter: plan=%r key=%r value=%f status=ok",
            plan_name,
            key,
            value,
        )
        return f"set parameter {key!r} = {value} on plan {plan_name!r}"

    @mcp.tool()
    def finance_get_plan_parameters(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
    ) -> dict[str, float]:
        """Return all registered central plan parameters."""
        plan = load_plan(working_directory, plan_name)
        logger.info("finance_get_plan_parameters: plan=%r status=ok", plan_name)
        return plan.parameters
