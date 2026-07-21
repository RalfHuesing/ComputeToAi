"""Advisory structural and logical consistency checks for plan audits.

See Docs/04-Feature-Finanzen-Methodik.md, "Pfad-Audit und Plausibilitätsprüfung".
"""

from typing import Literal

from pydantic import BaseModel

from compute_to_ai.engine.effect import ComputedEffect, Effect, GrowingFixedEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import LedgerEntry, SimulationResult
from compute_to_ai.engine.timeline import Phase

_TAX_FUNCTION_NAMES = frozenset({"pension_income_tax_manager", "capital_gains_tax_manager"})
CategoryName = Literal["income", "expenses", "taxes", "returns", "reallocations"]


class AuditFinding(BaseModel):
    """One advisory, non-fatal finding from `audit_plan`."""

    step: int | None = None
    message: str


def _liability_store_names(plan: Plan) -> set[str]:
    names: set[str] = set()
    for effect in plan.effects:
        if isinstance(effect, ComputedEffect) and effect.function_name == "liability_manager":
            store = effect.parameters.get("liability_store_name")
            if isinstance(store, str):
                names.add(store)
    return names


def _classify_entry(entry: LedgerEntry, liability_stores: set[str]) -> tuple[CategoryName, float]:
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


def _check_overlapping_income(
    result: SimulationResult, liability_stores: set[str]
) -> list[AuditFinding]:
    by_step_store: dict[tuple[int, str], list[LedgerEntry]] = {}
    for entry in result.ledger:
        category, _ = _classify_entry(entry, liability_stores)
        if category != "income":
            continue
        by_step_store.setdefault((entry.step, entry.store_name), []).append(entry)

    findings: list[AuditFinding] = []
    for (step, store_name), entries in by_step_store.items():
        if len(entries) < 2:
            continue
        names = ", ".join(sorted({entry.effect_name for entry in entries}))
        findings.append(
            AuditFinding(
                step=step,
                message=(
                    f"multiple income effects ({names}) target store {store_name!r} "
                    "in the same step - check for an unintended overlap (e.g. a "
                    "phase-transition off-by-one)"
                ),
            )
        )
    return findings


def _check_income_less_phase(
    plan: Plan, result: SimulationResult, liability_stores: set[str]
) -> list[AuditFinding]:
    if not plan.ruin_stores:
        return []

    income_steps: set[int] = set()
    for entry in result.ledger:
        if entry.store_name not in plan.ruin_stores:
            continue
        category, _ = _classify_entry(entry, liability_stores)
        if category == "income":
            income_steps.add(entry.step)

    findings: list[AuditFinding] = []
    for phase in plan.phases:
        last_step = min(phase.end_step, plan.timeline.step_count) - 1
        if last_step < phase.start_step:
            continue
        if not any(t in income_steps for t in range(phase.start_step, last_step + 1)):
            findings.append(
                AuditFinding(
                    step=phase.start_step,
                    message=(
                        f"phase {phase.name!r} (steps {phase.start_step}-{last_step}) has no "
                        f"income-category activity on any target-condition store "
                        f"{sorted(plan.ruin_stores)} - verify this is intentional"
                    ),
                )
            )
    return findings


def _effect_overlaps_phase(effect: Effect, phase: Phase, step_count: int) -> bool:
    active_phases = effect.active_phases
    if active_phases is not None and phase.name not in active_phases:
        return False
    eff_start = effect.start_step or 0
    eff_end_raw = effect.end_step
    eff_end = eff_end_raw if eff_end_raw is not None else step_count - 1
    return eff_start <= phase.end_step - 1 and eff_end >= phase.start_step


def _income_expense_rates_in_phase(
    plan: Plan, phase: Phase, step_count: int
) -> tuple[list[float], list[float]]:
    income_rates: list[float] = []
    expense_rates: list[float] = []
    for effect in plan.effects:
        if not isinstance(effect, GrowingFixedEffect):
            continue
        start_step = effect.start_step
        end_step = effect.end_step
        if start_step is not None and start_step == end_step:
            continue
        if not _effect_overlaps_phase(effect, phase, step_count):
            continue
        amount = effect.amount_per_step
        rate = effect.growth_rate
        if amount > 0.0:
            income_rates.append(rate)
        elif amount < 0.0:
            expense_rates.append(rate)
    return income_rates, expense_rates


def _check_growth_inflation_mismatch(plan: Plan) -> list[AuditFinding]:
    step_count = plan.timeline.step_count
    findings: list[AuditFinding] = []

    for phase in plan.phases:
        income_rates, expense_rates = _income_expense_rates_in_phase(plan, phase, step_count)
        if not income_rates or not expense_rates:
            continue
        if any(r > 0.0 for r in income_rates) and any(r == 0.0 for r in expense_rates):
            findings.append(
                AuditFinding(
                    step=phase.start_step,
                    message=(
                        f"phase {phase.name!r}: at least one income effect grows "
                        "(growth_rate > 0) while at least one expense effect has "
                        "inflation_rate=0.0 - the savings rate will drift structurally "
                        "over time even if the starting values look reasonable"
                    ),
                )
            )
        if any(r > 0.0 for r in expense_rates) and any(r == 0.0 for r in income_rates):
            findings.append(
                AuditFinding(
                    step=phase.start_step,
                    message=(
                        f"phase {phase.name!r}: at least one expense effect grows "
                        "(inflation_rate > 0) while at least one income effect has "
                        "growth_rate=0.0 - the savings rate will drift structurally "
                        "over time even if the starting values look reasonable"
                    ),
                )
            )
    return findings


def _check_orphaned_stores(plan: Plan, result: SimulationResult) -> list[AuditFinding]:
    touched = {entry.store_name for entry in result.ledger}
    return [
        AuditFinding(
            step=None,
            message=(
                f"store {store.name!r} is never touched by any effect across the whole "
                "timeline - check whether it's still connected to the plan"
            ),
        )
        for store in plan.stores
        if store.name not in touched
    ]


def _check_unpaid_liabilities(
    result: SimulationResult, liability_stores: set[str]
) -> list[AuditFinding]:
    if not result.time_series:
        return []
    final_balances = result.time_series[-1]
    findings: list[AuditFinding] = []
    for store_name in sorted(liability_stores):
        balance = final_balances.get(store_name, 0.0)
        if balance > 1e-6:
            findings.append(
                AuditFinding(
                    step=len(result.time_series) - 1,
                    message=(
                        f"liability store {store_name!r} still has a balance of "
                        f"{balance:.2f} at the end of the timeline - it will not be fully "
                        "paid off"
                    ),
                )
            )
    return findings


def audit_plan(plan: Plan, result: SimulationResult) -> list[AuditFinding]:
    """Run a fixed set of structural/logical consistency checks on one path."""
    liability_stores = _liability_store_names(plan)
    findings = [
        *_check_overlapping_income(result, liability_stores),
        *_check_income_less_phase(plan, result, liability_stores),
        *_check_growth_inflation_mismatch(plan),
        *_check_orphaned_stores(plan, result),
        *_check_unpaid_liabilities(result, liability_stores),
    ]
    return sorted(findings, key=lambda finding: (finding.step is None, finding.step or 0))
