"""Cashflow (income, expenses, acquisitions) MCP tools.

Mutating tools echo the actually stored (possibly converted) values back as
a structured dict instead of a plain confirmation string, so the caller can
verify e.g. the frequency-folded `amount_per_step` against its own input
(see Docs/02-Architektur-und-MCP.md, "Baustein-Katalog").
"""

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.cashflow import (
    add_expense,
    add_fixed_acquisition,
    add_flexible_acquisition,
    add_income_stream,
)
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan

logger = logging.getLogger(__name__)


def register_cashflow_tools(mcp: FastMCP, working_directory: Path) -> None:
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
    ) -> dict[str, Any]:
        """Add a growing income stream (positive cashflow) to the plan.

        `frequency`/`interval_years` are relative to the plan's own step
        granularity (`Timeline.steps_per_year`, set via core_create_plan),
        not to calendar months - e.g. "monthly" on a plan with one step per
        year folds 12 months into the full annual `amount_per_step`, applied
        every step, rather than spacing it out.

        Returns the stored effect's values, including the frequency-folded
        `amount_per_step` (which may differ from `amount`).
        """
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
        effect = plan.effects[-1]
        logger.info("finance_add_income_stream: plan=%r name=%r status=ok", plan_name, name)
        logger.debug("finance_add_income_stream stored effect: %s", effect.model_dump())
        return {
            "name": effect.name,
            "store_name": store_name,
            "amount_per_step": getattr(effect, "amount_per_step", None),
            "interval_steps": effect.interval_steps,
            "first_occurrence_step": effect.first_occurrence_step,
            "start_step": effect.start_step,
            "end_step": effect.end_step,
        }

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
    ) -> dict[str, Any]:
        """Add an inflation-adjusted expense (negative cashflow) to the plan.

        `frequency`/`interval_years` are relative to the plan's own step
        granularity (`Timeline.steps_per_year`, set via core_create_plan),
        not to calendar months - see finance_add_income_stream.

        Returns the stored effect's values, including the frequency-folded,
        negated `amount_per_step` (which may differ from `amount`).
        """
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
        effect = plan.effects[-1]
        logger.info("finance_add_expense: plan=%r name=%r status=ok", plan_name, name)
        logger.debug("finance_add_expense stored effect: %s", effect.model_dump())
        return {
            "name": effect.name,
            "store_name": store_name,
            "amount_per_step": getattr(effect, "amount_per_step", None),
            "interval_steps": effect.interval_steps,
            "first_occurrence_step": effect.first_occurrence_step,
            "start_step": effect.start_step,
            "end_step": effect.end_step,
        }

    @mcp.tool()
    def finance_add_fixed_acquisition(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        name: str,
        store_name: str,
        amount: float,
        step: int,
        inflation_rate: float = 0.0,
        description: str | None = None,
        glidepath_years: float = 0.0,
        risky_store_name: str | None = None,
    ) -> dict[str, Any]:
        """Add a one-time fixed acquisition (always an outflow, magnitude only).

        With `glidepath_years > 0` and a `risky_store_name`, capital is
        gradually shifted from `risky_store_name` into `store_name` over the
        glidepath window preceding `step` (stored as a `flexible_acquisition`
        computed effect); otherwise a plain one-step outflow is stored.

        Returns the stored effect's values, including which effect type was
        created and the negated `amount_per_step` for the plain variant.
        """
        plan = load_plan(working_directory, plan_name)
        add_fixed_acquisition(
            plan,
            name,
            store_name,
            amount,
            step,
            inflation_rate,
            description,
            glidepath_years,
            risky_store_name,
        )
        save_plan(working_directory, plan)
        effect = plan.effects[-1]
        logger.info("finance_add_fixed_acquisition: plan=%r name=%r status=ok", plan_name, name)
        logger.debug("finance_add_fixed_acquisition stored effect: %s", effect.model_dump())
        parameters = getattr(effect, "parameters", None)
        if parameters is not None:
            return {
                "name": effect.name,
                "effect_type": "flexible_acquisition",
                "amount": parameters.get("amount"),
                "target_step": parameters.get("target_step"),
                "glidepath_start_step": parameters.get("glidepath_start_step"),
                "risky_store_name": parameters.get("risky_store_name"),
                "safe_store_name": parameters.get("safe_store_name"),
            }
        return {
            "name": effect.name,
            "effect_type": "growing_fixed",
            "store_name": store_name,
            "amount_per_step": getattr(effect, "amount_per_step", None),
            "start_step": effect.start_step,
            "end_step": effect.end_step,
        }

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
    ) -> dict[str, Any]:
        """Add a flexible acquisition with reference-path trigger and glidepath de-risking.

        Returns the stored computed-effect parameters, including the
        normalized (absolute) `amount`.
        """
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
        effect = plan.effects[-1]
        parameters = getattr(effect, "parameters", {})
        logger.info("finance_add_flexible_acquisition: plan=%r name=%r status=ok", plan_name, name)
        logger.debug("finance_add_flexible_acquisition stored effect: %s", effect.model_dump())
        return {
            "name": effect.name,
            "amount": parameters.get("amount"),
            "target_step": parameters.get("target_step"),
            "tolerance_steps": parameters.get("tolerance_steps"),
            "glidepath_start_step": parameters.get("glidepath_start_step"),
            "risky_store_name": parameters.get("risky_store_name"),
            "safe_store_name": parameters.get("safe_store_name"),
        }
