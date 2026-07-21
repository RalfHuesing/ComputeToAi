"""Path audit, explanation, and plan comparison MCP tools."""

import logging
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import MonteCarloResult, PathAuditResult, SimulationResult
from compute_to_ai.features.finance.compare import compare_plans
from compute_to_ai.features.finance.path_audit import (
    audit_plan,
    build_event_log,
    compute_category_series,
    get_percentile_curves,
)
from compute_to_ai.mcp.tools.plan_storage import (
    PATH_AUDIT_RESULT_FILENAME,
    ResultNotFoundError,
    load_audited_path,
    load_plan,
    load_result,
)

logger = logging.getLogger(__name__)

_MONTE_CARLO_RESULT_FILENAME = "monte_carlo_result.json"


def _load_audited_path(
    working_directory: Path, plan_name: str, path: str
) -> tuple[Plan, SimulationResult]:
    plan = load_plan(working_directory, plan_name)
    result = load_audited_path(working_directory, plan_name, path)
    return plan, result


def register_path_audit_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_get_path_category_series(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        path: str,
        granularity: Literal[
            "annual", "monthly_average", "annual_real", "monthly_average_real"
        ] = "annual",
    ) -> dict[str, Any]:
        """Return per-step cashflow category sums for one path of the plan's path audit."""
        plan, result = _load_audited_path(working_directory, plan_name, path)
        series = compute_category_series(plan, result, granularity)
        logger.info("finance_get_path_category_series: plan=%r path=%r status=ok", plan_name, path)
        return {"steps": [step.model_dump() for step in series]}

    @mcp.tool()
    def finance_get_path_event_log(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, path: str
    ) -> dict[str, Any]:
        """Return the chronological event log for one path of the plan's path audit."""
        plan, result = _load_audited_path(working_directory, plan_name, path)
        events = build_event_log(plan, result)
        logger.info("finance_get_path_event_log: plan=%r path=%r status=ok", plan_name, path)
        return {"events": [event.model_dump() for event in events]}

    @mcp.tool()
    def finance_audit_plan(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, path: str = "deterministic"
    ) -> dict[str, Any]:
        """Run structural/logical consistency checks on one path of the plan's path audit."""
        plan, result = _load_audited_path(working_directory, plan_name, path)
        findings = audit_plan(plan, result)
        logger.info(
            "finance_audit_plan: plan=%r path=%r findings=%d status=ok",
            plan_name,
            path,
            len(findings),
        )
        return {"findings": [finding.model_dump() for finding in findings]}

    @mcp.tool()
    def finance_compare_plans(  # pyright: ignore[reportUnusedFunction]
        plan_name_a: str, plan_name_b: str
    ) -> dict[str, Any]:
        """Compare two plans, identifying configuration changes and simulation outcome deltas."""
        plan_a = load_plan(working_directory, plan_name_a)
        plan_b = load_plan(working_directory, plan_name_b)

        try:
            result_a = load_result(
                working_directory, plan_name_a, _MONTE_CARLO_RESULT_FILENAME, MonteCarloResult
            )
        except ResultNotFoundError:
            result_a = None

        try:
            result_b = load_result(
                working_directory, plan_name_b, _MONTE_CARLO_RESULT_FILENAME, MonteCarloResult
            )
        except ResultNotFoundError:
            result_b = None

        comparison = compare_plans(plan_a, result_a, plan_b, result_b)
        logger.info(
            "finance_compare_plans: plan_a=%r plan_b=%r status=ok", plan_name_a, plan_name_b
        )
        return comparison

    @mcp.tool()
    def finance_get_percentile_curves(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
    ) -> dict[str, Any]:
        """Return the aggregated liquid, invested, liabilities, and net worth curves."""
        plan = load_plan(working_directory, plan_name)
        audit = load_result(
            working_directory, plan_name, PATH_AUDIT_RESULT_FILENAME, PathAuditResult
        )
        curves = get_percentile_curves(plan, audit)
        logger.info("finance_get_percentile_curves: plan=%r status=ok", plan_name)
        return {"curves": curves}
