"""Liabilities and extra payments MCP tools.

Mutating tools echo the actually stored values back as a structured dict
instead of a plain confirmation string (see Docs/02-Architektur-und-MCP.md,
"Baustein-Katalog").
"""

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.liability import ScheduledExtraPayment, add_liability
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan

logger = logging.getLogger(__name__)


def register_liability_tools(mcp: FastMCP, working_directory: Path) -> None:
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
    ) -> dict[str, Any]:
        """Add a liability (loan/mortgage) with regular payments and optional Sondertilgung.

        Returns the stored values, including the liability store's opening
        balance and the names of the effects the building block created.
        """
        plan = load_plan(working_directory, plan_name)
        effect_count_before = len(plan.effects)
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
        added_effects = plan.effects[effect_count_before:]
        logger.info("finance_add_liability: plan=%r name=%r status=ok", plan_name, name)
        logger.debug(
            "finance_add_liability stored effects: %s",
            [effect.model_dump() for effect in added_effects],
        )
        return {
            "name": name,
            "liability_store_name": liability_store_name,
            "liability_balance": plan.store(liability_store_name).balance,
            "cash_store_name": cash_store_name,
            "interest_rate": interest_rate,
            "payment_per_step": payment,
            "start_step": start_step,
            "end_step": end_step,
            "effects_added": [effect.name for effect in added_effects],
        }
