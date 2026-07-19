"""Finance tools: income/expenses, liabilities, portfolio, tax, pension, phases.

See Docs/02-Architektur-und-MCP.md for the `finance_` tool-name prefix and
Docs/03/04/05-Feature-Finanzen-*.md for the underlying concepts. Each tool
is a thin load-plan / call-building-block / save-plan wrapper around the
`compute_to_ai.features.finance` building blocks; no financial logic lives
here (see "Trennung der Verantwortlichkeiten" in
Docs/11-Code-Standards-und-Projektstruktur.md).

INFO-level logs stay free of concrete financial figures; DEBUG-level logs
carry the full arguments/results (see "Logging" in Docs/02 and
.agents/rules/mcp-server-architecture.mdc).
"""

import logging
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import MonteCarloResult, SimulationResult
from compute_to_ai.engine.simulation import run_monte_carlo
from compute_to_ai.features.finance.cashflow import (
    add_expense,
    add_fixed_acquisition,
    add_flexible_acquisition,
    add_income_stream,
)
from compute_to_ai.features.finance.liability import ScheduledExtraPayment, add_liability
from compute_to_ai.features.finance.path_audit import (
    audit_plan,
    build_event_log,
    compute_category_series,
)
from compute_to_ai.features.finance.pension import (
    add_statutory_pension,
    calculate_pension_adjustment_factor,
)
from compute_to_ai.features.finance.phases import build_standard_life_phases
from compute_to_ai.features.finance.portfolio import (
    add_asset_class,
    add_cash_bucket,
    add_portfolio_rebalancing,
    set_correlation_matrix,
)
from compute_to_ai.features.finance.tax import AssetClassTaxConfig, IncomeTaxTariff, add_tax_manager
from compute_to_ai.mcp.tools.plan_storage import (
    load_audited_path,
    load_plan,
    load_result,
    save_plan,
    save_result,
)

logger = logging.getLogger(__name__)

_MONTE_CARLO_RESULT_FILENAME = "monte_carlo_result.json"


def register_finance_tools(mcp: FastMCP, working_directory: Path) -> None:
    """Register the finance building-block, goal-condition, and Monte-Carlo tools."""
    _register_phase_tools(mcp, working_directory)
    _register_cashflow_tools(mcp, working_directory)
    _register_liability_tools(mcp, working_directory)
    _register_portfolio_tools(mcp, working_directory)
    _register_tax_and_pension_tools(mcp, working_directory)
    _register_goal_and_monte_carlo_tools(mcp, working_directory)
    _register_path_audit_tools(mcp, working_directory)


def _register_phase_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_set_life_phases(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        current_age: int,
        employment_end_age: int,
        statutory_pension_start_age: int,
        life_expectancy_age: int,
        education_end_age: int | None = None,
    ) -> str:
        """Set the plan's phases to the standard life-phase sequence (Docs/05, "Lebensphasen")."""
        plan = load_plan(working_directory, plan_name)
        plan.phases = build_standard_life_phases(
            current_age=current_age,
            employment_end_age=employment_end_age,
            statutory_pension_start_age=statutory_pension_start_age,
            life_expectancy_age=life_expectancy_age,
            education_end_age=education_end_age,
        )
        save_plan(working_directory, plan)
        logger.info("finance_set_life_phases: plan=%r status=ok", plan_name)
        logger.debug("finance_set_life_phases args: %s", [p.model_dump() for p in plan.phases])
        return f"set {len(plan.phases)} life phases on plan {plan_name!r}"


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
    ) -> str:
        """Add a growing income stream (positive cashflow) to the plan."""
        plan = load_plan(working_directory, plan_name)
        add_income_stream(
            plan, name, store_name, amount, growth_rate, active_phases, start_step, end_step, description
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
    ) -> str:
        """Add an inflation-adjusted expense (negative cashflow) to the plan."""
        plan = load_plan(working_directory, plan_name)
        add_expense(
            plan, name, store_name, amount, inflation_rate, active_phases, start_step, end_step, description
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
        """Add a one-time fixed acquisition (always an outflow, magnitude only).

        A one-time windfall (Sondereinnahme, e.g. an inheritance) is a
        positive cashflow, not a negative acquisition - use
        finance_add_income_stream with start_step==end_step for that instead
        (see Docs/03-Feature-Finanzen-Domaenenmodell.md, "Anschaffung").
        """
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
    ) -> str:
        """Add an asset class with a correlated stochastic return effect to the plan."""
        plan = load_plan(working_directory, plan_name)
        add_asset_class(
            plan, store_name, initial_balance, expected_return, volatility, correlation_group, description
        )
        save_plan(working_directory, plan)
        logger.info("finance_add_asset_class: plan=%r store=%r status=ok", plan_name, store_name)
        return f"added asset class {store_name!r} to plan {plan_name!r}"

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
    ) -> str:
        """Add a computed rebalancing effect that keeps asset classes at target weights."""
        plan = load_plan(working_directory, plan_name)
        add_portfolio_rebalancing(plan, name, weights, start_step, end_step, description)
        save_plan(working_directory, plan)
        logger.info("finance_add_portfolio_rebalancing: plan=%r name=%r status=ok", plan_name, name)
        return f"added portfolio rebalancing {name!r} to plan {plan_name!r}"

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
    ) -> str:
        """Add the Cash-Bucket manager (liquidity buffer sizing and rebalancing).

        `max_target_cash` caps the dynamically computed target size, so
        excess cash above the cap still sweeps into the portfolio but the
        target itself never grows past it.
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
        logger.info("finance_add_cash_bucket: plan=%r status=ok", plan_name)
        return f"added cash bucket manager to plan {plan_name!r}"


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
        """Add the statutory pension (gesetzliche Rente) including Rentenabschlag/-zuschlag.

        `annual_amount_at_regular_retirement_age` is the yearly figure, matching
        every other finance_add_* amount (a monthly pension quote must be
        multiplied by 12 before calling this tool).
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
        """Adjusted pension for claiming early/late (Rentenabschlag/-zuschlag),
        without needing a Plan - the same calculation add_statutory_pension applies
        internally, for a quick standalone check (e.g. "what if I retire 5 years early?").

        `base_amount` is a pure multiplicative-factor calculation, not tied to
        the simulation's step convention - pass a monthly or yearly figure,
        the returned value is adjusted in the same unit.
        """
        factor = calculate_pension_adjustment_factor(
            months_early=months_early,
            months_late=months_late,
            early_reduction_rate_per_month=early_reduction_rate_per_month,
            early_reduction_cap=early_reduction_cap,
            late_bonus_rate_per_month=late_bonus_rate_per_month,
        )
        logger.info("finance_calculate_pension_adjustment: status=ok")
        return base_amount * factor


def _register_goal_and_monte_carlo_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_set_target_condition(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, ruin_stores: list[str], ruin_threshold: float = 0.0
    ) -> str:
        """Set the goal condition: which stores' combined balance must stay >= ruin_threshold.

        There is no separate "target success probability" setting - that's a
        property of the Monte-Carlo result (1 - ruin_probability), not of the
        plan, so it's read from finance_get_monte_carlo_result instead of
        configured here.
        """
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


def _load_audited_path(
    working_directory: Path, plan_name: str, path: str
) -> tuple[Plan, SimulationResult]:
    """Load the plan and one named path from its last path audit, or raise ValueError."""
    plan = load_plan(working_directory, plan_name)
    result = load_audited_path(working_directory, plan_name, path)
    return plan, result


def _register_path_audit_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_get_path_category_series(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        path: str,
        granularity: Literal["annual", "monthly_average"] = "annual",
    ) -> dict[str, Any]:
        """Return per-step cashflow category sums (Einnahmen, Ausgaben, Steuern,
        Rendite, Umschichtungen, Saldo je Speicher) for one path of the plan's
        last path audit (see core_run_path_audit).

        `path` is one of the labels from core_run_path_audit's result (e.g.
        "p50", "p10", "deterministic"). `granularity="monthly_average"`
        divides every flow category by 12 for easier comparison against a
        monthly household budget.
        """
        plan, result = _load_audited_path(working_directory, plan_name, path)
        series = compute_category_series(plan, result, granularity)
        logger.info(
            "finance_get_path_category_series: plan=%r path=%r status=ok", plan_name, path
        )
        return {"steps": [step.model_dump() for step in series]}

    @mcp.tool()
    def finance_get_path_event_log(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, path: str
    ) -> dict[str, Any]:
        """Return the chronological event log (phase transitions, liabilities
        paid off, acquisitions triggered) for one path of the plan's last
        path audit (see core_run_path_audit).
        """
        plan, result = _load_audited_path(working_directory, plan_name, path)
        events = build_event_log(plan, result)
        logger.info("finance_get_path_event_log: plan=%r path=%r status=ok", plan_name, path)
        return {"events": [event.model_dump() for event in events]}

    @mcp.tool()
    def finance_audit_plan(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, path: str = "deterministic"
    ) -> dict[str, Any]:
        """Run a fixed set of structural/logical consistency checks on one
        path of the plan's last path audit (see core_run_path_audit) and
        return the findings as advisory hints - not hard errors, since the
        flagged configuration may be entirely intentional.

        Checks: overlapping income effects hitting the same store in the
        same step, a phase with no income activity on a target-condition
        store, a growing income next to a flat expense (or vice versa)
        within a phase, a store never touched by any effect, and a
        liability not fully paid off by the end of the timeline (see
        Docs/10-Roadmap.md, Epic 3.10, for the full rationale). No
        magnitude/domain-knowledge judgment is made here - that remains the
        agent's own job.
        """
        plan, result = _load_audited_path(working_directory, plan_name, path)
        findings = audit_plan(plan, result)
        logger.info(
            "finance_audit_plan: plan=%r path=%r findings=%d status=ok",
            plan_name,
            path,
            len(findings),
        )
        return {"findings": [finding.model_dump() for finding in findings]}
