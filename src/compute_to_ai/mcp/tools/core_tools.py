"""Core tools: Plan/Store/Effect/Simulation - see Docs/02-Architektur-und-MCP.md.

INFO-level logs stay free of concrete financial figures; DEBUG-level logs
carry the full arguments/results (see "Logging" in Docs/02 and
.agents/rules/mcp-server-architecture.mdc). Tool names carry a `core_`
prefix, the "Kern-Tools" category from Docs/02's tool hierarchy.
"""

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.engine.effect import FixedEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import SimulationResult
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline

logger = logging.getLogger(__name__)


def _plan_file(working_directory: Path, plan_name: str) -> Path:
    return working_directory / plan_name / "plan.json"


def _result_file(working_directory: Path, plan_name: str) -> Path:
    return working_directory / plan_name / "result.json"


def _load_plan(working_directory: Path, plan_name: str) -> Plan:
    plan_file = _plan_file(working_directory, plan_name)
    if not plan_file.exists():
        msg = f"no plan named {plan_name!r}; create it first with core_create_plan"
        raise ValueError(msg)
    return Plan.model_validate_json(plan_file.read_text(encoding="utf-8"))


def _save_plan(working_directory: Path, plan: Plan) -> None:
    plan_file = _plan_file(working_directory, plan.name)
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    plan_file.write_text(plan.model_dump_json(indent=2), encoding="utf-8")


def register_core_tools(mcp: FastMCP, working_directory: Path) -> None:
    """Register the core Plan/Store/Effect/Simulation tools."""

    @mcp.tool()
    def core_create_plan(plan_name: str, step_count: int) -> str:  # pyright: ignore[reportUnusedFunction]
        """Create a new Plan with an empty Timeline of step_count steps."""
        plan = Plan(name=plan_name, timeline=Timeline(step_count=step_count))
        _save_plan(working_directory, plan)
        logger.info("core_create_plan: plan=%r status=ok", plan_name)
        logger.debug("core_create_plan args: step_count=%d", step_count)
        return f"created plan {plan_name!r} with {step_count} steps"

    @mcp.tool()
    def core_add_store(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, store_name: str, initial_balance: float = 0.0
    ) -> str:
        """Add a Store (a tracked balance) to an existing Plan."""
        plan = _load_plan(working_directory, plan_name)
        plan.stores.append(Store(name=store_name, balance=initial_balance))
        _save_plan(working_directory, plan)
        logger.info("core_add_store: plan=%r store=%r status=ok", plan_name, store_name)
        logger.debug("core_add_store args: initial_balance=%s", initial_balance)
        return f"added store {store_name!r} to plan {plan_name!r}"

    @mcp.tool()
    def core_add_effect(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, store_name: str, amount_per_step: float
    ) -> str:
        """Add a fixed per-step Effect on a Store in an existing Plan."""
        plan = _load_plan(working_directory, plan_name)
        plan.store(store_name)  # raises KeyError if store_name is unknown
        plan.effects.append(FixedEffect(store_name=store_name, amount_per_step=amount_per_step))
        _save_plan(working_directory, plan)
        logger.info("core_add_effect: plan=%r store=%r status=ok", plan_name, store_name)
        logger.debug("core_add_effect args: amount_per_step=%s", amount_per_step)
        return f"added effect on store {store_name!r} to plan {plan_name!r}"

    @mcp.tool()
    def core_run_simulation(plan_name: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Run the deterministic simulation for a Plan."""
        plan = _load_plan(working_directory, plan_name)
        result = run_simulation(plan)
        result_file = _result_file(working_directory, plan_name)
        result_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        logger.info("core_run_simulation: plan=%r status=ok", plan_name)
        logger.debug("core_run_simulation result: %s", result.final_balances)
        return f"simulation for plan {plan_name!r} complete"

    @mcp.tool()
    def core_get_result(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, include_time_series: bool = False
    ) -> dict[str, Any]:
        """Return the final balances (and optionally the time series) of a Plan's last run."""
        result_file = _result_file(working_directory, plan_name)
        if not result_file.exists():
            msg = f"no result for plan {plan_name!r}; call core_run_simulation first"
            raise ValueError(msg)
        result = SimulationResult.model_validate_json(result_file.read_text(encoding="utf-8"))
        logger.info("core_get_result: plan=%r status=ok", plan_name)
        payload = (
            result.model_dump()
            if include_time_series
            else {"final_balances": result.final_balances}
        )
        logger.debug("core_get_result payload: %s", payload)
        return payload
