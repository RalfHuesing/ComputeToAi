"""Finance-specific interpretation of a generic engine path-audit result.

Classifies an instrumented run's per-step ledger into cashflow categories
and derives a chronological event log - the "Explainable AI"
plausibility-check building blocks described in
Docs/04-Feature-Finanzen-Methodik.md, "Pfad-Audit und Plausibilitätsprüfung".
The engine itself (see Docs/01-Kern-Domaenenmodell.md, "Ledger") assigns no
income/expense/tax meaning to a ledger entry - that classification lives
here, not in `compute_to_ai.engine`.
"""

from typing import Literal

from pydantic import BaseModel

from compute_to_ai.engine.effect import (
    ComputedEffect,
    CorrelatedReturnEffect,
    GrowingFixedEffect,
)
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import LedgerEntry, PathAuditResult, SimulationResult
from compute_to_ai.features.finance._audit_checks import AuditFinding, audit_plan

__all__ = [
    "AuditFinding",
    "CategoryStep",
    "PathEvent",
    "audit_plan",
    "build_event_log",
    "compute_category_series",
    "get_percentile_curves",
    "liability_store_names",
]

CategoryName = Literal["income", "expenses", "taxes", "returns", "reallocations"]



_TAX_FUNCTION_NAMES = frozenset({"pension_income_tax_manager", "capital_gains_tax_manager"})


class CategoryStep(BaseModel):
    """Per-step cashflow category sums for one instrumented path.

    `balances` is a direct snapshot of that step's per-store balance (Saldo)
    - not itself a flow category, kept alongside the five flow categories
    for a single, self-contained per-step record.
    """

    step: int
    income: float = 0.0
    expenses: float = 0.0
    taxes: float = 0.0
    returns: float = 0.0
    reallocations: float = 0.0
    balances: dict[str, float] = {}


class PathEvent(BaseModel):
    """One chronological event in a path's event log."""

    step: int
    event_type: Literal["phase_transition", "liability_paid_off", "acquisition_triggered"]
    description: str


def liability_store_names(plan: Plan) -> set[str]:
    """Collect every store backing a `liability_manager` building block.

    Deltas on these stores (interest accrual, principal reduction) restate
    the liability's own remaining balance - the real cash outflow already
    shows up once, as the "Rate" expense on the cash store (see
    Docs/04-Feature-Finanzen-Methodik.md) - so counting them again here
    would double-count the same payment as both an expense and an
    (independent) reduction of the liability.
    """
    names: set[str] = set()
    for effect in plan.effects:
        if isinstance(effect, ComputedEffect) and effect.function_name == "liability_manager":
            store = effect.parameters.get("liability_store_name")
            if isinstance(store, str):
                names.add(store)
    return names


def _classify_entry(entry: LedgerEntry, liability_stores: set[str]) -> tuple[CategoryName, float]:
    """Map one ledger entry to (category, signed magnitude in that category)."""
    if entry.effect_type == "computed":
        if entry.function_name in _TAX_FUNCTION_NAMES:
            return "taxes", -entry.delta
        return "reallocations", entry.delta

    if (
        entry.effect_type in ("percentage_growth", "correlated_return")
        or entry.store_name in liability_stores
    ):
        cat: CategoryName = "reallocations" if entry.store_name in liability_stores else "returns"
        return cat, entry.delta

    if entry.delta > 0.0:
        return "income", entry.delta
    return "expenses", -entry.delta


def _find_plan_inflation_rate(plan: Plan) -> float:
    """Find the inflation rate of a plan from its effects configuration."""
    for effect in plan.effects:
        if isinstance(effect, ComputedEffect) and effect.function_name == "cash_bucket_manager":
            val = effect.parameters.get("inflation_rate", 0.0)
            if isinstance(val, float):
                return val
    for effect in plan.effects:
        if isinstance(effect, GrowingFixedEffect) and effect.name == "Lebenshaltung":
            return float(effect.growth_rate)
    return 0.0


def compute_category_series(
    plan: Plan,
    result: SimulationResult,
    granularity: Literal[
        "annual", "monthly_average", "annual_real", "monthly_average_real"
    ] = "annual",
) -> list[CategoryStep]:
    """Aggregate an instrumented run's ledger into per-step category sums.

    See module docstring and Docs/04-Feature-Finanzen-Methodik.md for the
    category scheme. `granularity="monthly_average"` divides every flow
    category (not `balances`, a point-in-time snapshot) by 12, for easier
    comparison against a monthly household budget.
    """
    liability_stores = liability_store_names(plan)
    steps = {
        t: CategoryStep(step=t, balances=dict(balances))
        for t, balances in enumerate(result.time_series)
    }

    for entry in result.ledger:
        category, magnitude = _classify_entry(entry, liability_stores)
        step_data = steps.setdefault(entry.step, CategoryStep(step=entry.step))
        setattr(step_data, category, getattr(step_data, category) + magnitude)

    is_real = granularity in ("annual_real", "monthly_average_real")
    divisor = 12.0 if granularity in ("monthly_average", "monthly_average_real") else 1.0
    inflation_rate = _find_plan_inflation_rate(plan) if is_real else 0.0

    return [
        CategoryStep(
            step=t,
            income=(steps[t].income / ((1.0 + inflation_rate) ** t)) / divisor,
            expenses=(steps[t].expenses / ((1.0 + inflation_rate) ** t)) / divisor,
            taxes=(steps[t].taxes / ((1.0 + inflation_rate) ** t)) / divisor,
            returns=(steps[t].returns / ((1.0 + inflation_rate) ** t)) / divisor,
            reallocations=(steps[t].reallocations / ((1.0 + inflation_rate) ** t)) / divisor,
            balances={
                store: bal / ((1.0 + inflation_rate) ** t)
                for store, bal in steps[t].balances.items()
            }
            if is_real
            else steps[t].balances,
        )
        for t in sorted(steps)
    ]


def _phase_transition_events(plan: Plan) -> list[PathEvent]:
    """One event per step where the active phase differs from the previous step."""
    events: list[PathEvent] = []
    previous = plan.get_active_phase_name(0)
    for t in range(1, plan.timeline.step_count):
        current = plan.get_active_phase_name(t)
        if current != previous:
            events.append(
                PathEvent(
                    step=t,
                    event_type="phase_transition",
                    description=f"active phase changed from {previous!r} to {current!r}",
                )
            )
            previous = current
    return events


def _liability_paid_off_events(plan: Plan, result: SimulationResult) -> list[PathEvent]:
    """One event per liability store, at the step its balance first reaches 0.

    Prepends the store's pre-simulation balance (`plan.store(...).balance`,
    unaffected by the run - see `_run_single_simulation`, which restores
    `plan.stores` in a `finally` block) so a liability paid off already
    during the very first step is detected too, not just from the second
    step onward.
    """
    events: list[PathEvent] = []
    for effect in plan.effects:
        if isinstance(effect, ComputedEffect) and effect.function_name == "liability_manager":
            store_name = effect.parameters.get("liability_store_name")
            if not isinstance(store_name, str):
                continue
            label = effect.name or store_name
            series = [plan.store(store_name).balance]
            series.extend(balances.get(store_name, 0.0) for balances in result.time_series)
            for k in range(1, len(series)):
                if series[k - 1] > 1e-6 and series[k] <= 1e-6:
                    events.append(
                        PathEvent(
                            step=k - 1,
                            event_type="liability_paid_off",
                            description=f"{label} paid off",
                        )
                    )
                    break
    return events


def _fixed_acquisition_events(plan: Plan, result: SimulationResult) -> list[PathEvent]:
    """One event per single-step, negative GrowingFixedEffect that actually fired.

    A fixed acquisition/Anschaffung is, structurally, a GrowingFixedEffect
    with `start_step == end_step` and a negative amount (see
    Docs/03-Feature-Finanzen-Domaenenmodell.md, "Anschaffung") - a positive
    single-step effect is a Sondereinnahme/windfall instead, out of scope
    for this event type. Confirmed via its ledger entry (rather than assumed
    from configuration alone) so a phase-restricted effect that never
    actually became active is correctly not reported as triggered.
    """
    fixed_acquisition_names: set[str] = set()
    for effect in plan.effects:
        if isinstance(effect, GrowingFixedEffect):
            start_step = effect.start_step
            end_step = effect.end_step
            amount = effect.amount_per_step
            if start_step is not None and start_step == end_step and amount < 0.0:
                fixed_acquisition_names.add(
                    effect.name if effect.name is not None else "growing_fixed"
                )

    return [
        PathEvent(
            step=entry.step,
            event_type="acquisition_triggered",
            description=f"fixed acquisition {entry.effect_name!r} triggered",
        )
        for entry in result.ledger
        if entry.effect_type == "growing_fixed" and entry.effect_name in fixed_acquisition_names
    ]


def _flexible_acquisition_events(result: SimulationResult) -> list[PathEvent]:
    """One event per flexible acquisition whose run-scoped `triggered_step` was set."""
    events: list[PathEvent] = []
    for state in result.computed_effect_final_states:
        if state.function_name != "flexible_acquisition":
            continue
        triggered_step = state.parameters.get("triggered_step")
        if isinstance(triggered_step, int):
            events.append(
                PathEvent(
                    step=triggered_step,
                    event_type="acquisition_triggered",
                    description=f"flexible acquisition {state.effect_name!r} triggered",
                )
            )
    return events


def build_event_log(plan: Plan, result: SimulationResult) -> list[PathEvent]:
    """Build the chronological event log for one instrumented path.

    Covers exactly three event types (see Docs/04-Feature-Finanzen-Methodik.md,
    "Pfad-Audit und Plausibilitätsprüfung"): phase transitions, a liability
    being paid off, and an acquisition (fixed or flexible) triggering.
    """
    events = [
        *_phase_transition_events(plan),
        *_liability_paid_off_events(plan, result),
        *_fixed_acquisition_events(plan, result),
        *_flexible_acquisition_events(result),
    ]
    return sorted(events, key=lambda event: event.step)


def get_percentile_curves(plan: Plan, audit: PathAuditResult) -> dict[str, list[dict[str, float]]]:
    """Classify all plan stores and return aggregated balance curves for each audited path."""
    liability_stores = liability_store_names(plan)
    invested_stores = {
        store_name
        for eff in plan.effects
        if isinstance(eff, CorrelatedReturnEffect)
        for store_name in eff.store_names
    }

    # Liquid stores are those that are neither liabilities nor asset classes
    all_store_names = {s.name for s in plan.stores}
    liquid_stores = all_store_names - liability_stores - invested_stores

    curves: dict[str, list[dict[str, float]]] = {}
    for path_name, path_result in audit.paths.items():
        steps_list: list[dict[str, float]] = []
        for t, balances in enumerate(path_result.time_series):
            liquid_balance = sum(balances.get(name, 0.0) for name in liquid_stores)
            invested_balance = sum(balances.get(name, 0.0) for name in invested_stores)
            liabilities_balance = sum(balances.get(name, 0.0) for name in liability_stores)

            steps_list.append(
                {
                    "step": float(t),
                    "liquid": liquid_balance,
                    "invested": invested_balance,
                    "liabilities": liabilities_balance,
                    "total_net": liquid_balance + invested_balance - liabilities_balance,
                }
            )
        curves[path_name] = steps_list

    return curves
