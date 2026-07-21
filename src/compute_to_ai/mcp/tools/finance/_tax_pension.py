"""Tax and pension MCP tools.

Mutating tools echo the actually stored (possibly computed) values back as
a structured dict instead of a plain confirmation string (see
Docs/02-Architektur-und-MCP.md, "Baustein-Katalog").
"""

import logging
from pathlib import Path
from typing import Any

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
    ) -> dict[str, Any]:
        """Add the German tax manager (Abgeltungsteuer, Vorabpauschale, Rentenbesteuerung).

        Returns the stored values, including the names of the computed
        effects the building block created.
        """
        plan = load_plan(working_directory, plan_name)
        effect_count_before = len(plan.effects)
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
        added_effects = plan.effects[effect_count_before:]
        logger.info("finance_add_tax_manager: plan=%r status=ok", plan_name)
        logger.debug(
            "finance_add_tax_manager stored effects: %s",
            [effect.model_dump() for effect in added_effects],
        )
        return {
            "cash_store_name": cash_store_name,
            "retirement_step": retirement_step,
            "start_year": start_year,
            "asset_classes": sorted(asset_classes) if asset_classes else [],
            "effects_added": [effect.name for effect in added_effects],
        }

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
    ) -> dict[str, Any]:
        """Add the statutory pension (gesetzliche Rente) including Rentenabschlag/-zuschlag.

        Returns the stored effect's values - most importantly the
        `annual_amount` actually applied per step, i.e. after the
        Rentenabschlag/-zuschlag adjustment (which may differ from
        `annual_amount_at_regular_retirement_age`).
        """
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
        effect = plan.effects[-1]
        logger.info("finance_add_statutory_pension: plan=%r name=%r status=ok", plan_name, name)
        logger.debug("finance_add_statutory_pension stored effect: %s", effect.model_dump())
        annual_amount = getattr(effect, "amount_per_step", None)
        adjustment_factor = (
            annual_amount / annual_amount_at_regular_retirement_age
            if annual_amount is not None and annual_amount_at_regular_retirement_age != 0.0
            else None
        )
        return {
            "name": effect.name,
            "store_name": store_name,
            "annual_amount": annual_amount,
            "adjustment_factor": adjustment_factor,
            "start_step": effect.start_step,
            "end_step": effect.end_step,
        }

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
