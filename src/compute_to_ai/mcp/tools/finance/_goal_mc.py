"""Goal conditions and Monte Carlo simulation MCP tools."""

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.engine.result import MonteCarloResult
from compute_to_ai.engine.simulation import run_monte_carlo
from compute_to_ai.mcp.tools.plan_storage import load_plan, load_result, save_plan, save_result

logger = logging.getLogger(__name__)

_MONTE_CARLO_RESULT_FILENAME = "monte_carlo_result.json"


def _register_goal_and_monte_carlo_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_set_target_condition(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, ruin_stores: list[str], ruin_threshold: float = 0.0
    ) -> str:
        """Set the goal condition: which stores' combined balance must stay >= ruin_threshold."""
        plan = load_plan(working_directory, plan_name)
        plan.ruin_stores = ruin_stores
        plan.ruin_threshold = ruin_threshold
        save_plan(working_directory, plan)
        logger.info("finance_set_target_condition: plan=%r status=ok", plan_name)
        return f"set target condition on plan {plan_name!r}"

    @mcp.tool()
    def finance_run_monte_carlo(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, num_runs: int, seed: int | None = None
    ) -> str:
        """Run a Monte-Carlo simulation with stochastically drawn correlated returns."""
        plan = load_plan(working_directory, plan_name)
        result = run_monte_carlo(plan, num_runs, seed)
        save_result(working_directory, plan_name, _MONTE_CARLO_RESULT_FILENAME, result)
        logger.info("finance_run_monte_carlo: plan=%r num_runs=%d status=ok", plan_name, num_runs)
        logger.debug("finance_run_monte_carlo result: ruin_probability=%s", result.ruin_probability)
        return f"Monte-Carlo simulation for plan {plan_name!r} complete ({num_runs} runs)"

    @mcp.tool()
    def finance_get_monte_carlo_result(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, include_raw_final_balances: bool = False
    ) -> dict[str, Any]:
        """Return the aggregated result (ruin probability, percentiles) of the last MC run."""
        result = load_result(
            working_directory, plan_name, _MONTE_CARLO_RESULT_FILENAME, MonteCarloResult
        )
        logger.info("finance_get_monte_carlo_result: plan=%r status=ok", plan_name)
        payload = result.model_dump()
        if not include_raw_final_balances:
            del payload["raw_final_balances"]
        logger.debug("finance_get_monte_carlo_result payload: %s", payload)
        return payload
