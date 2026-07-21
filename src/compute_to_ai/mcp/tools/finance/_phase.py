"""Life phase MCP tools."""

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.phases import build_standard_life_phases
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan

logger = logging.getLogger(__name__)


def _register_phase_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_set_life_phases(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        current_age: int,
        employment_end_age: int,
        statutory_pension_start_age: int,
        life_expectancy_age: int,
        education_end_age: int | None = None,
    ) -> str:
        """Set the plan's phases to the standard life-phase sequence."""
        plan = load_plan(working_directory, plan_name)
        plan.phases = build_standard_life_phases(
            current_age=current_age,
            employment_end_age=employment_end_age,
            statutory_pension_start_age=statutory_pension_start_age,
            life_expectancy_age=life_expectancy_age,
            education_end_age=education_end_age,
        )
        save_plan(working_directory, plan)
        logger.info("finance_set_life_phases: plan=%r status=ok", plan_name)
        logger.debug("finance_set_life_phases args: %s", [p.model_dump() for p in plan.phases])
        return f"set {len(plan.phases)} life phases on plan {plan_name!r}"
