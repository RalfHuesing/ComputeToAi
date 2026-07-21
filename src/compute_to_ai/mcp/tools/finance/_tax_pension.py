"""Tax and pension MCP tools."""

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.pension import (
    add_statutory_pension,
    calculate_pension_adjustment_factor,
)
from compute_to_ai.features.finance.tax import AssetClassTaxConfig, IncomeTaxTariff, add_tax_manager
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan

logger = logging.getLogger(__name__)


def _register_tax_and_pension_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_add_tax_manager(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        cash_store_name: str = "cash",
        sparerpauschbetrag: float = 1000.0,
        basiszins: float = 0.032,
        withholding_tax_rate: float = 0.25,
        soli_rate: float = 0.055,
        church_tax_rate: float = 0.0,
        tariff: IncomeTaxTariff | None = None,
        kvdr_rate: float = 0.0875,
        pv_rate: float = 0.042,
        retirement_step: int = 47,
        start_year: int = 2026,
        asset_classes: dict[str, AssetClassTaxConfig] | None = None,
        description: str | None = None,
    ) -> str:
        """Add the German tax manager (Abgeltungsteuer, Vorabpauschale, Rentenbesteuerung)."""
        plan = load_plan(working_directory, plan_name)
        add_tax_manager(
            plan,
            cash_store_name,
            sparerpauschbetrag,
            basiszins,
            withholding_tax_rate,
            soli_rate,
            church_tax_rate,
            tariff,
            kvdr_rate,
            pv_rate,
            retirement_step,
            start_year,
            asset_classes,
            description,
        )
        save_plan(working_directory, plan)
        logger.info("finance_add_tax_manager: plan=%r status=ok", plan_name)
        return f"added tax manager to plan {plan_name!r}"

    @mcp.tool()
    def finance_add_statutory_pension(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        name: str,
        store_name: str,
        annual_amount_at_regular_retirement_age: float,
        regular_retirement_step: int,
        actual_retirement_step: int,
        annual_increase_rate: float = 0.0,
        early_reduction_rate_per_month: float = 0.003,
        early_reduction_cap: float = 0.144,
        late_bonus_rate_per_month: float = 0.005,
        active_phases: list[str] | None = None,
        end_step: int | None = None,
        description: str | None = None,
    ) -> str:
        """Add the statutory pension (gesetzliche Rente) including Rentenabschlag/-zuschlag."""
        plan = load_plan(working_directory, plan_name)
        add_statutory_pension(
            plan,
            name,
            store_name,
            annual_amount_at_regular_retirement_age,
            regular_retirement_step,
            actual_retirement_step,
            annual_increase_rate,
            early_reduction_rate_per_month,
            early_reduction_cap,
            late_bonus_rate_per_month,
            active_phases,
            end_step,
            description,
        )
        save_plan(working_directory, plan)
        logger.info("finance_add_statutory_pension: plan=%r name=%r status=ok", plan_name, name)
        return f"added statutory pension {name!r} to plan {plan_name!r}"

    @mcp.tool()
    def finance_calculate_pension_adjustment(  # pyright: ignore[reportUnusedFunction]
        base_amount: float,
        months_early: float = 0.0,
        months_late: float = 0.0,
        early_reduction_rate_per_month: float = 0.003,
        early_reduction_cap: float = 0.144,
        late_bonus_rate_per_month: float = 0.005,
    ) -> float:
        """Adjusted pension for claiming early/late (Rentenabschlag/-zuschlag)."""
        factor = calculate_pension_adjustment_factor(
            months_early=months_early,
            months_late=months_late,
            early_reduction_rate_per_month=early_reduction_rate_per_month,
            early_reduction_cap=early_reduction_cap,
            late_bonus_rate_per_month=late_bonus_rate_per_month,
        )
        logger.info("finance_calculate_pension_adjustment: status=ok")
        return base_amount * factor
