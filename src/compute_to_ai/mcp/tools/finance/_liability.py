"""Liabilities and extra payments MCP tools."""

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.liability import ScheduledExtraPayment, add_liability
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan

logger = logging.getLogger(__name__)


def _register_liability_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_add_liability(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        name: str,
        liability_store_name: str,
        cash_store_name: str,
        principal: float,
        interest_rate: float,
        payment: float,
        start_step: int = 0,
        end_step: int | None = None,
        extra_payment_amount: float = 0.0,
        extra_payment_threshold_rate: float | None = None,
        extra_payment_min_cash: float = 0.0,
        extra_payments: list[ScheduledExtraPayment] | None = None,
        description: str | None = None,
    ) -> str:
        """Add a liability (loan/mortgage) with regular payments and optional Sondertilgung."""
        plan = load_plan(working_directory, plan_name)
        add_liability(
            plan,
            name,
            liability_store_name,
            cash_store_name,
            principal,
            interest_rate,
            payment,
            start_step,
            end_step,
            extra_payment_amount,
            extra_payment_threshold_rate,
            extra_payment_min_cash,
            extra_payments,
            description,
        )
        save_plan(working_directory, plan)
        logger.info("finance_add_liability: plan=%r name=%r status=ok", plan_name, name)
        return f"added liability {name!r} to plan {plan_name!r}"
