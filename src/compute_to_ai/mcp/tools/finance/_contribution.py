"""Savings rate contribution recommendation MCP tools."""

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.portfolio import suggest_contribution_allocation
from compute_to_ai.mcp.tools.plan_storage import load_plan

logger = logging.getLogger(__name__)


def register_contribution_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_suggest_contribution_allocation(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, new_amount: float
    ) -> dict[str, Any]:
        """Suggest how to split a new contribution across asset classes."""
        plan = load_plan(working_directory, plan_name)
        suggestions = suggest_contribution_allocation(plan, new_amount)

        logger.info(
            "finance_suggest_contribution_allocation: plan=%r suggestions=%d status=ok",
            plan_name,
            len(suggestions),
        )
        logger.debug(
            "finance_suggest_contribution_allocation result: %s",
            [s.model_dump() for s in suggestions],
        )
        return {"suggestions": [s.model_dump() for s in suggestions]}
