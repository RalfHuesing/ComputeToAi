"""Cashflow (income, expenses, acquisitions) MCP tools."""

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.cashflow import (
    add_expense,
    add_fixed_acquisition,
    add_flexible_acquisition,
    add_income_stream,
)
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan

logger = logging.getLogger(__name__)


def _register_cashflow_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_add_income_stream(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        name: str,
        store_name: str,
        amount: float,
        growth_rate: float = 0.0,
        active_phases: list[str] | None = None,
        start_step: int | None = None,
        end_step: int | None = None,
        description: str | None = None,
        frequency: str = "monthly",
        interval_years: int | None = None,
        first_occurrence_step: int = 0,
        first_occurrence_year: float | None = None,
    ) -> str:
        """Add a growing income stream (positive cashflow) to the plan."""
        plan = load_plan(working_directory, plan_name)
        add_income_stream(
            plan,
            name,
            store_name,
            amount,
            growth_rate,
            active_phases,
            start_step,
            end_step,
            description,
            frequency,
            interval_years,
            first_occurrence_step,
            first_occurrence_year,
        )
        save_plan(working_directory, plan)
        logger.info("finance_add_income_stream: plan=%r name=%r status=ok", plan_name, name)
        return f"added income stream {name!r} to plan {plan_name!r}"

    @mcp.tool()
    def finance_add_expense(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        name: str,
        store_name: str,
        amount: float,
        inflation_rate: float = 0.0,
        active_phases: list[str] | None = None,
        start_step: int | None = None,
        end_step: int | None = None,
        description: str | None = None,
        frequency: str = "monthly",
        interval_years: int | None = None,
        first_occurrence_step: int = 0,
        first_occurrence_year: float | None = None,
    ) -> str:
        """Add an inflation-adjusted expense (negative cashflow) to the plan."""
        plan = load_plan(working_directory, plan_name)
        add_expense(
            plan,
            name,
            store_name,
            amount,
            inflation_rate,
            active_phases,
            start_step,
            end_step,
            description,
            frequency,
            interval_years,
            first_occurrence_step,
            first_occurrence_year,
        )
        save_plan(working_directory, plan)
        logger.info("finance_add_expense: plan=%r name=%r status=ok", plan_name, name)
        return f"added expense {name!r} to plan {plan_name!r}"

    @mcp.tool()
    def finance_add_fixed_acquisition(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        name: str,
        store_name: str,
        amount: float,
        step: int,
        inflation_rate: float = 0.0,
        description: str | None = None,
    ) -> str:
        """Add a one-time fixed acquisition (always an outflow, magnitude only)."""
        plan = load_plan(working_directory, plan_name)
        add_fixed_acquisition(plan, name, store_name, amount, step, inflation_rate, description)
        save_plan(working_directory, plan)
        logger.info("finance_add_fixed_acquisition: plan=%r name=%r status=ok", plan_name, name)
        return f"added fixed acquisition {name!r} to plan {plan_name!r}"

    @mcp.tool()
    def finance_add_flexible_acquisition(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        name: str,
        amount: float,
        target_step: int,
        tolerance_steps: int,
        risky_store_name: str,
        safe_store_name: str,
        glidepath_start_step: int,
        inflation_rate: float = 0.0,
        description: str | None = None,
    ) -> str:
        """Add a flexible acquisition with reference-path trigger and glidepath de-risking."""
        plan = load_plan(working_directory, plan_name)
        add_flexible_acquisition(
            plan,
            name,
            amount,
            target_step,
            tolerance_steps,
            risky_store_name,
            safe_store_name,
            glidepath_start_step,
            inflation_rate,
            description,
        )
        save_plan(working_directory, plan)
        logger.info("finance_add_flexible_acquisition: plan=%r name=%r status=ok", plan_name, name)
        return f"added flexible acquisition {name!r} to plan {plan_name!r}"
