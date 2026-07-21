"""Portfolio and asset class allocation MCP tools.

Mutating tools echo the actually stored values back as a structured dict
instead of a plain confirmation string (see Docs/02-Architektur-und-MCP.md,
"Baustein-Katalog").
"""

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.portfolio import (
    add_asset_class,
    add_cash_bucket,
    add_portfolio_rebalancing,
    set_correlation_matrix,
)
from compute_to_ai.features.finance.positions_rebalancing import add_position_rebalancing
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan

logger = logging.getLogger(__name__)


def _register_portfolio_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_add_asset_class(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        store_name: str,
        initial_balance: float,
        expected_return: float,
        volatility: float,
        correlation_group: str = "portfolio",
        description: str | None = None,
    ) -> dict[str, Any]:
        """Add an asset class with a correlated stochastic return effect to the plan.

        Returns the stored values, including the store's actual balance
        (which keeps its prior value if the store already existed).
        """
        plan = load_plan(working_directory, plan_name)
        add_asset_class(
            plan,
            store_name,
            initial_balance,
            expected_return,
            volatility,
            correlation_group,
            description,
        )
        save_plan(working_directory, plan)
        effect = plan.effects[-1]
        logger.info("finance_add_asset_class: plan=%r store=%r status=ok", plan_name, store_name)
        logger.debug("finance_add_asset_class stored effect: %s", effect.model_dump())
        return {
            "store_name": store_name,
            "balance": plan.store(store_name).balance,
            "expected_return": expected_return,
            "volatility": volatility,
            "correlation_group": correlation_group,
            "effect_name": effect.name,
        }

    @mcp.tool()
    def finance_set_correlation_matrix(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, group_name: str, matrix: list[list[float]], store_names: list[str]
    ) -> str:
        """Set the correlation matrix for a named correlation group (e.g. asset classes)."""
        plan = load_plan(working_directory, plan_name)
        set_correlation_matrix(plan, group_name, matrix, store_names)
        save_plan(working_directory, plan)
        logger.info(
            "finance_set_correlation_matrix: plan=%r group=%r status=ok", plan_name, group_name
        )
        return f"set correlation matrix {group_name!r} on plan {plan_name!r}"

    @mcp.tool()
    def finance_add_portfolio_rebalancing(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        name: str,
        weights: dict[str, float],
        start_step: int = 0,
        end_step: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Add a computed rebalancing effect that keeps asset classes at target weights.

        Returns the stored effect's values (target weights and active window).
        """
        plan = load_plan(working_directory, plan_name)
        add_portfolio_rebalancing(plan, name, weights, start_step, end_step, description)
        save_plan(working_directory, plan)
        effect = plan.effects[-1]
        parameters = getattr(effect, "parameters", {})
        logger.info("finance_add_portfolio_rebalancing: plan=%r name=%r status=ok", plan_name, name)
        logger.debug("finance_add_portfolio_rebalancing stored effect: %s", effect.model_dump())
        return {
            "name": effect.name,
            "weights": parameters.get("weights"),
            "start_step": effect.start_step,
            "end_step": effect.end_step,
        }

    @mcp.tool()
    def finance_add_position_rebalancing(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        store_names: list[str],
        active_store_name: str,
        sell_threshold: float | None = None,
        description: str | None = None,
    ) -> str:
        """Add positions-rebalancing within one asset class's positions."""
        plan = load_plan(working_directory, plan_name)
        add_position_rebalancing(plan, store_names, active_store_name, sell_threshold, description)
        save_plan(working_directory, plan)
        logger.info(
            "finance_add_position_rebalancing: plan=%r active_store_name=%r status=ok",
            plan_name,
            active_store_name,
        )
        return f"added position rebalancing (active={active_store_name!r}) to plan {plan_name!r}"

    @mcp.tool()
    def finance_add_cash_bucket(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        portfolio_weights: dict[str, float],
        emergency_buffer_months: dict[str, float],
        monthly_expenses: float,
        inflation_rate: float = 0.0,
        near_horizon_steps: int = 2,
        withdrawal_years: float = 3.0,
        cash_store_name: str = "cash",
        withdrawal_phase_names: list[str] | None = None,
        max_target_cash: float | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Add the Cash-Bucket manager (liquidity buffer sizing and rebalancing).

        Returns the stored manager parameters (including defaults that were
        filled in), so the caller can verify the configuration it created.
        """
        plan = load_plan(working_directory, plan_name)
        add_cash_bucket(
            plan,
            portfolio_weights,
            emergency_buffer_months,
            monthly_expenses,
            inflation_rate,
            near_horizon_steps,
            withdrawal_years,
            cash_store_name,
            withdrawal_phase_names,
            max_target_cash,
            description,
        )
        save_plan(working_directory, plan)
        effect = plan.effects[-1]
        parameters = getattr(effect, "parameters", {})
        logger.info("finance_add_cash_bucket: plan=%r status=ok", plan_name)
        logger.debug("finance_add_cash_bucket stored effect: %s", effect.model_dump())
        return {"name": effect.name, "parameters": parameters}
