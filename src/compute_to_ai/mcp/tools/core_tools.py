"""Core tools: Plan/Store/Effect/Simulation - see Docs/02-Architektur-und-MCP.md.

INFO-level logs stay free of concrete financial figures; DEBUG-level logs
carry the full arguments/results (see "Logging" in Docs/02 and
.agents/rules/mcp-server-architecture.mdc). Tool names carry a `core_`
prefix, the "Kern-Tools" category from Docs/02's tool hierarchy.
"""

import logging
import shutil
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.engine.effect import GrowingFixedEffect, TransferEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import SimulationResult
from compute_to_ai.engine.simulation import run_path_audit, run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline
from compute_to_ai.mcp.tools.plan_storage import PATH_AUDIT_RESULT_FILENAME
from compute_to_ai.mcp.tools.plan_storage import load_audited_path as _load_audited_path
from compute_to_ai.mcp.tools.plan_storage import load_plan as _load_plan
from compute_to_ai.mcp.tools.plan_storage import load_result as _load_result
from compute_to_ai.mcp.tools.plan_storage import plan_dir as _plan_dir
from compute_to_ai.mcp.tools.plan_storage import save_plan as _save_plan
from compute_to_ai.mcp.tools.plan_storage import save_result as _save_result

logger = logging.getLogger(__name__)

_RESULT_FILENAME = "result.json"


def register_core_tools(mcp: FastMCP, working_directory: Path) -> None:
    """Register the core Plan/Store/Effect/Simulation tools."""
    _register_plan_lifecycle_tools(mcp, working_directory)
    _register_plan_editing_tools(mcp, working_directory)
    _register_simulation_tools(mcp, working_directory)


def _register_plan_lifecycle_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def core_create_plan(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        step_count: int,
        steps_per_year: int = 12,
        description: str | None = None,
    ) -> str:
        """Create a new Plan with an empty Timeline of step_count steps.

        `steps_per_year` fixes how many steps make up one calendar year
        (default 12, i.e. monthly steps) - feature-module tools that accept a
        calendar-based `frequency` (e.g. finance_add_income_stream) convert
        relative to this value, so a Plan built on annual steps (one step per
        simulated year) must set it to 1.
        """
        plan = Plan(
            name=plan_name,
            timeline=Timeline(step_count=step_count, steps_per_year=steps_per_year),
            description=description,
        )
        _save_plan(working_directory, plan)
        logger.info("core_create_plan: plan=%r status=ok", plan_name)
        logger.debug(
            "core_create_plan args: step_count=%d steps_per_year=%d", step_count, steps_per_year
        )
        return f"created plan {plan_name!r} with {step_count} steps"

    @mcp.tool()
    def core_set_steps_per_year(plan_name: str, steps_per_year: int) -> str:  # pyright: ignore[reportUnusedFunction]
        """Change how many steps make up one calendar year on an existing Plan.

        Does not rescale existing effects - amounts/intervals already stored
        via finance_add_income_stream etc. keep their stored values, which
        may now mean something different (e.g. a "yearly"-frequency effect
        added under steps_per_year=12 keeps firing every 12 steps even after
        this is changed to 1). Intended for correcting a wrong value early,
        before effects are added - not for reinterpreting an already-built
        plan.
        """
        if steps_per_year <= 0:
            msg = f"steps_per_year must be > 0, got {steps_per_year}"
            raise ValueError(msg)
        plan = _load_plan(working_directory, plan_name)
        plan.timeline.steps_per_year = steps_per_year
        _save_plan(working_directory, plan)
        logger.info(
            "core_set_steps_per_year: plan=%r steps_per_year=%d status=ok",
            plan_name,
            steps_per_year,
        )
        return f"set steps_per_year={steps_per_year} on plan {plan_name!r}"

    @mcp.tool()
    def core_duplicate_plan(plan_name: str, new_plan_name: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Copy a plan's configuration under a new name (for What-if variants).

        Only the configuration is copied, not past simulation results - a
        duplicate is meant to be tweaked and (re-)simulated, so carrying over
        a stale result would misleadingly look like it already reflects the
        copy's own configuration.
        """
        if _plan_dir(working_directory, new_plan_name).exists():
            msg = f"a plan named {new_plan_name!r} already exists"
            raise ValueError(msg)
        plan = _load_plan(working_directory, plan_name)
        new_plan = plan.model_copy(deep=True)
        new_plan.name = new_plan_name
        _save_plan(working_directory, new_plan)
        logger.info("core_duplicate_plan: plan=%r new_plan=%r status=ok", plan_name, new_plan_name)
        return f"duplicated plan {plan_name!r} as {new_plan_name!r}"

    @mcp.tool()
    def core_rename_plan(plan_name: str, new_plan_name: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Rename a plan, moving its files (including any past results)."""
        old_dir = _plan_dir(working_directory, plan_name)
        new_dir = _plan_dir(working_directory, new_plan_name)
        if not old_dir.exists():
            msg = f"no plan named {plan_name!r}"
            raise ValueError(msg)
        if new_dir.exists():
            msg = f"a plan named {new_plan_name!r} already exists"
            raise ValueError(msg)
        plan = _load_plan(working_directory, plan_name)
        shutil.move(str(old_dir), str(new_dir))
        plan.name = new_plan_name
        _save_plan(working_directory, plan)
        logger.info("core_rename_plan: plan=%r new_plan=%r status=ok", plan_name, new_plan_name)
        return f"renamed plan {plan_name!r} to {new_plan_name!r}"

    @mcp.tool()
    def core_delete_plan(plan_name: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Permanently delete a plan and all its files (configuration and results)."""
        plan_directory = _plan_dir(working_directory, plan_name)
        if not plan_directory.exists():
            msg = f"no plan named {plan_name!r}"
            raise ValueError(msg)
        shutil.rmtree(plan_directory)
        logger.info("core_delete_plan: plan=%r status=ok", plan_name)
        return f"deleted plan {plan_name!r}"


def _validate_transfer_targets(
    plan: Plan, from_store_name: str, to_store_weights: dict[str, float]
) -> None:
    """Raise ValueError for an unknown store or if weights don't sum to 1.0."""
    plan.validate_store_names([from_store_name, *to_store_weights])
    weight_sum = sum(to_store_weights.values())
    if abs(weight_sum - 1.0) > 1e-9:
        msg = f"to_store_weights must sum to 1.0, got {weight_sum!r}"
        raise ValueError(msg)


def _register_plan_editing_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def core_add_store(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        store_name: str,
        initial_balance: float = 0.0,
        description: str | None = None,
    ) -> str:
        """Add a Store (a tracked balance) to an existing Plan."""
        plan = _load_plan(working_directory, plan_name)
        plan.stores.append(Store(name=store_name, balance=initial_balance, description=description))
        _save_plan(working_directory, plan)
        logger.info("core_add_store: plan=%r store=%r status=ok", plan_name, store_name)
        logger.debug("core_add_store args: initial_balance=%s", initial_balance)
        return f"added store {store_name!r} to plan {plan_name!r}"

    @mcp.tool()
    def core_add_effect(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        store_name: str,
        name: str,
        amount_per_step: float,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Add a fixed per-step Effect on a Store in an existing Plan.

        `name` is mandatory (unlike the optional `name` on the underlying
        Effect model) - core_remove_effect can only look an effect up by
        name, so an effect added without one could never be removed again.

        Returns the stored effect's values as a structured echo.
        """
        plan = _load_plan(working_directory, plan_name)
        plan.store(store_name)  # raises KeyError if store_name is unknown
        effect = GrowingFixedEffect(
            name=name,
            store_name=store_name,
            amount_per_step=amount_per_step,
            description=description,
        )
        plan.effects.append(effect)
        _save_plan(working_directory, plan)
        logger.info(
            "core_add_effect: plan=%r store=%r effect=%r status=ok", plan_name, store_name, name
        )
        logger.debug("core_add_effect stored effect: %s", effect.model_dump())
        return {
            "name": effect.name,
            "store_name": effect.store_name,
            "amount_per_step": effect.amount_per_step,
            "start_step": effect.start_step,
            "end_step": effect.end_step,
        }

    @mcp.tool()
    def core_add_transfer(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        from_store_name: str,
        to_store_weights: dict[str, float],
        amount: float,
        growth_rate: float = 0.0,
        active_phases: list[str] | None = None,
        start_step: int | None = None,
        end_step: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Add a per-step Transfer effect between Stores in an existing Plan.

        Moves a fixed (optionally growing) amount from one Store, split
        across one or more destination Stores by weight - e.g. a fixed
        savings rate into a portfolio, without a negative-expense/
        positive-income workaround.

        Returns the stored effect's values, including the normalized
        (absolute) `amount_per_step`.
        """
        plan = _load_plan(working_directory, plan_name)
        _validate_transfer_targets(plan, from_store_name, to_store_weights)
        plan.validate_active_phases(active_phases)
        effect = TransferEffect(
            from_store_name=from_store_name,
            to_store_weights=to_store_weights,
            amount_per_step=abs(amount),
            growth_rate=growth_rate,
            active_phases=active_phases,
            start_step=start_step,
            end_step=end_step,
            description=description,
        )
        plan.effects.append(effect)
        _save_plan(working_directory, plan)
        logger.info("core_add_transfer: plan=%r from=%r status=ok", plan_name, from_store_name)
        logger.debug("core_add_transfer stored effect: %s", effect.model_dump())
        return {
            "from_store_name": effect.from_store_name,
            "to_store_weights": effect.to_store_weights,
            "amount_per_step": effect.amount_per_step,
            "growth_rate": effect.growth_rate,
            "start_step": effect.start_step,
            "end_step": effect.end_step,
        }

    @mcp.tool()
    def core_list_stores(plan_name: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """List every Store in a Plan, including its balance and lots."""
        plan = _load_plan(working_directory, plan_name)
        logger.info("core_list_stores: plan=%r status=ok", plan_name)
        return {"stores": [store.model_dump() for store in plan.stores]}

    @mcp.tool()
    def core_list_effects(plan_name: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """List every Effect in a Plan, including its name, type and parameters."""
        plan = _load_plan(working_directory, plan_name)
        logger.info("core_list_effects: plan=%r status=ok", plan_name)
        return {"effects": [effect.model_dump() for effect in plan.effects]}

    @mcp.tool()
    def core_list_phases(plan_name: str) -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
        """List every Phase in a Plan, including its name, step boundaries and description."""
        plan = _load_plan(working_directory, plan_name)
        logger.info("core_list_phases: plan=%r status=ok", plan_name)
        return {"phases": [phase.model_dump() for phase in plan.phases]}

    @mcp.tool()
    def core_remove_effect(plan_name: str, effect_name: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Remove the Effect with this exact name from a Plan.

        Use core_list_effects first to see what's configured. Fails if no
        effect (or more than one) matches the name, rather than guessing -
        an "update" is achieved by removing and adding again.
        """
        plan = _load_plan(working_directory, plan_name)
        matches = [effect for effect in plan.effects if effect.name == effect_name]
        if not matches:
            msg = f"no effect named {effect_name!r} in plan {plan_name!r}"
            raise ValueError(msg)
        if len(matches) > 1:
            msg = (
                f"{len(matches)} effects named {effect_name!r} in plan {plan_name!r} - "
                "ambiguous, cannot remove"
            )
            raise ValueError(msg)
        plan.effects = [effect for effect in plan.effects if effect.name != effect_name]
        _save_plan(working_directory, plan)
        logger.info("core_remove_effect: plan=%r effect=%r status=ok", plan_name, effect_name)
        return f"removed effect {effect_name!r} from plan {plan_name!r}"


def _register_simulation_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def core_run_simulation(plan_name: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Run the deterministic simulation for a Plan."""
        plan = _load_plan(working_directory, plan_name)
        result = run_simulation(plan)
        _save_result(working_directory, plan_name, _RESULT_FILENAME, result)
        logger.info("core_run_simulation: plan=%r status=ok", plan_name)
        logger.debug("core_run_simulation result: %s", result.final_balances)
        return f"simulation for plan {plan_name!r} complete"

    @mcp.tool()
    def core_get_result(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, include_time_series: bool = False
    ) -> dict[str, Any]:
        """Return the final balances (and optionally the time series) of a Plan's last run."""
        result = _load_result(working_directory, plan_name, _RESULT_FILENAME, SimulationResult)
        logger.info("core_get_result: plan=%r status=ok", plan_name)
        payload = (
            result.model_dump()
            if include_time_series
            else {
                "final_balances": result.final_balances,
                "ruin_step": result.ruin_step,
                "ruin_shortfall": result.ruin_shortfall,
            }
        )
        logger.debug("core_get_result payload: %s", payload)
        return payload

    @mcp.tool()
    def core_run_path_audit(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        num_runs: int,
        seed: int | None = None,
        percentiles: list[int] | None = None,
        store_names: list[str] | None = None,
    ) -> str:
        """Run a Monte-Carlo simulation, then instrument a few representative
        paths (one per percentile, plus the deterministic reference run)
        with a full per-step ledger, for later plausibility auditing.

        `store_names` defaults to the plan's target-condition stores (see
        finance_set_target_condition), falling back to every store in the
        plan if that's empty too. `percentiles` defaults to [50, 10] (median
        and worst-case-ish path).
        """
        plan = _load_plan(working_directory, plan_name)
        result = run_path_audit(
            plan,
            num_runs,
            seed,
            tuple(percentiles) if percentiles is not None else (50, 10),
            store_names,
        )
        _save_result(working_directory, plan_name, PATH_AUDIT_RESULT_FILENAME, result)
        logger.info(
            "core_run_path_audit: plan=%r num_runs=%d paths=%s status=ok",
            plan_name,
            num_runs,
            sorted(result.paths),
        )
        return f"path audit for plan {plan_name!r} complete ({', '.join(sorted(result.paths))})"

    @mcp.tool()
    def core_get_path_step_ledger(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, path: str, step: int
    ) -> dict[str, Any]:
        """Return the raw per-(Effect, Store) ledger entries for one step of
        one path of the plan's last path audit (see core_run_path_audit).

        No domain meaning (income/expense/tax/...) is attached here - the
        engine itself assigns none (see Docs/01-Kern-Domaenenmodell.md,
        "Ledger"); use finance_get_path_category_series for that. This is a
        drill-down for when a category sum itself needs explaining.
        """
        result = _load_audited_path(working_directory, plan_name, path)
        entries = [entry for entry in result.ledger if entry.step == step]
        logger.info(
            "core_get_path_step_ledger: plan=%r path=%r step=%d status=ok",
            plan_name,
            path,
            step,
        )
        return {"entries": [entry.model_dump() for entry in entries]}

    @mcp.tool()
    def core_get_path_computed_states(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, path: str
    ) -> dict[str, Any]:
        """Return the post-run parameter state of every ComputedEffect for
        one path of the plan's last path audit (see core_run_path_audit).

        Surfaces run-scoped mutable state a computed effect wrote into its
        own parameters during the run (e.g. whether/when a flexible
        acquisition triggered) - state otherwise not visible via MCP at all
        (see Docs/01-Kern-Domaenenmodell.md, "Ledger").
        """
        result = _load_audited_path(working_directory, plan_name, path)
        logger.info("core_get_path_computed_states: plan=%r path=%r status=ok", plan_name, path)
        return {"states": [state.model_dump() for state in result.computed_effect_final_states]}
