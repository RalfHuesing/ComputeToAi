"""Auswertungen and reports MCP tools."""

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.engine.result import PathAuditResult
from compute_to_ai.features.finance.reports import (
    compare_plan_actuals,
    estimate_sale_tax,
    get_asset_allocation_report,
)
from compute_to_ai.mcp.tools.plan_storage import (
    PATH_AUDIT_RESULT_FILENAME,
    ResultNotFoundError,
    load_plan,
    load_result,
)
from compute_to_ai.mcp.tools.position_storage import load_position_registry

logger = logging.getLogger(__name__)


def _register_report_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_get_asset_allocation_report(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
    ) -> dict[str, Any]:
        """Return target vs actual asset allocation, drift, and unrealized gains breakdown."""
        plan = load_plan(working_directory, plan_name)
        registry = load_position_registry(working_directory, plan_name)
        report = get_asset_allocation_report(plan, position_registry=registry)
        logger.info("finance_get_asset_allocation_report: plan=%r status=ok", plan_name)
        return report

    @mcp.tool()
    def finance_estimate_sale_tax(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        store_name: str,
        shares_to_sell: float | None = None,
        amount_to_sell: float | None = None,
        sell_all: bool = False,
        remaining_savers_allowance: float = 1000.0,
        church_tax_rate: float = 0.0,
    ) -> dict[str, Any]:
        """Estimate taxes for a hypothetical sale of shares or EUR amount of a position."""
        plan = load_plan(working_directory, plan_name)
        registry = load_position_registry(working_directory, plan_name)
        result = estimate_sale_tax(
            plan=plan,
            store_name=store_name,
            position_registry=registry,
            shares_to_sell=shares_to_sell,
            amount_to_sell=amount_to_sell,
            sell_all=sell_all,
            remaining_savers_allowance=remaining_savers_allowance,
            church_tax_rate=church_tax_rate,
        )
        logger.info("finance_estimate_sale_tax: plan=%r store=%r status=ok", plan_name, store_name)
        return result

    @mcp.tool()
    def finance_compare_plan_actuals(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        current_step: int = 0,
    ) -> dict[str, Any]:
        """Compare current total net worth against Monte Carlo percentile curves (p10, p50, p90)."""
        plan = load_plan(working_directory, plan_name)
        try:
            audit = load_result(
                working_directory, plan_name, PATH_AUDIT_RESULT_FILENAME, PathAuditResult
            )
        except ResultNotFoundError:
            audit = None

        result = compare_plan_actuals(plan, audit_result=audit, current_step=current_step)
        logger.info(
            "finance_compare_plan_actuals: plan=%r step=%d status=ok", plan_name, current_step
        )
        return result
