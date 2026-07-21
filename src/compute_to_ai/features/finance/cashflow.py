"""Financial cashflow components (income, expense, acquisitions).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

from pydantic import BaseModel

from compute_to_ai.engine.effect import (
    ComputedEffect,
    GrowingFixedEffect,
    register_computed_effect,
)
from compute_to_ai.engine.plan import Plan

FREQUENCY_PERIODS_PER_YEAR: dict[str, float] = {
    "monthly": 12.0,
    "quarterly": 4.0,
    "yearly": 1.0,
    "annual": 1.0,
}


def resolve_frequency(
    frequency: str = "monthly",
    steps_per_year: int = 12,
    interval_years: int | None = None,
) -> tuple[int, float]:
    """Resolve a frequency string into (interval_steps, amount_multiplier).

    A Plan's step is its finest resolvable unit of time (see
    `Timeline.steps_per_year`), so a frequency is never both scaled and
    spaced out. A frequency finer than one step (e.g. "monthly" on a
    Plan with `steps_per_year=1`) folds its occurrences within one step
    into `amount_multiplier`, applied every step (`interval_steps=1`). A
    frequency coarser than one step (e.g. "yearly" on a Plan with
    `steps_per_year=12`) instead spaces occurrences via `interval_steps`,
    leaving `amount_multiplier=1.0` since only one occurrence happens per
    firing.
    """
    freq = frequency.lower()
    if freq in FREQUENCY_PERIODS_PER_YEAR:
        periods_per_year = FREQUENCY_PERIODS_PER_YEAR[freq]
    elif freq == "every_n_years":
        if interval_years is None or interval_years < 1:
            msg = "interval_years must be at least 1 when frequency is 'every_n_years'"
            raise ValueError(msg)
        periods_per_year = 1.0 / interval_years
    else:
        supported = [*FREQUENCY_PERIODS_PER_YEAR.keys(), "every_n_years"]
        msg = f"Unknown frequency: {frequency!r}. Supported values: {supported}"
        raise ValueError(msg)

    occurrences_per_step = periods_per_year / steps_per_year
    if occurrences_per_step >= 1.0:
        return 1, occurrences_per_step
    return round(1.0 / occurrences_per_step), 1.0


def add_income_stream(
    plan: Plan,
    name: str,
    store_name: str,
    amount: float,
    growth_rate: float = 0.0,
    active_phases: list[str] | None = None,
    start_step: int | None = None,
    end_step: int | None = None,
    description: str | None = None,
    frequency: str = "monthly",
    interval_years: int | None = None,
    first_occurrence_step: int = 0,
    first_occurrence_year: float | None = None,
) -> None:
    """Add a growing fixed income stream (positive cashflow) to the plan.

    `store_name` references an existing Store and is validated up front - a
    typo'd name would otherwise create an effect the simulation silently
    never applies.
    """
    plan.validate_active_phases(active_phases)
    plan.validate_store_names([store_name])
    steps_per_year = plan.timeline.steps_per_year
    interval_steps, amount_multiplier = resolve_frequency(frequency, steps_per_year, interval_years)
    if first_occurrence_year is not None:
        first_occurrence_step = round(first_occurrence_year * steps_per_year)

    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=amount * amount_multiplier,
        growth_rate=growth_rate,
        active_phases=active_phases,
        start_step=start_step,
        end_step=end_step,
        description=description,
        interval_steps=interval_steps,
        first_occurrence_step=first_occurrence_step,
    )
    plan.effects.append(effect)


def add_expense(
    plan: Plan,
    name: str,
    store_name: str,
    amount: float,
    inflation_rate: float = 0.0,
    active_phases: list[str] | None = None,
    start_step: int | None = None,
    end_step: int | None = None,
    description: str | None = None,
    frequency: str = "monthly",
    interval_years: int | None = None,
    first_occurrence_step: int = 0,
    first_occurrence_year: float | None = None,
) -> None:
    """Add an inflation-adjusted expense (negative cashflow) to the plan.

    `store_name` references an existing Store and is validated up front - a
    typo'd name would otherwise create an effect the simulation silently
    never applies.
    """
    plan.validate_active_phases(active_phases)
    plan.validate_store_names([store_name])
    steps_per_year = plan.timeline.steps_per_year
    interval_steps, amount_multiplier = resolve_frequency(frequency, steps_per_year, interval_years)
    if first_occurrence_year is not None:
        first_occurrence_step = round(first_occurrence_year * steps_per_year)

    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=-amount * amount_multiplier,
        growth_rate=inflation_rate,
        active_phases=active_phases,
        start_step=start_step,
        end_step=end_step,
        description=description,
        interval_steps=interval_steps,
        first_occurrence_step=first_occurrence_step,
    )
    plan.effects.append(effect)


def add_fixed_acquisition(
    plan: Plan,
    name: str,
    store_name: str,
    amount: float,
    step: int,
    inflation_rate: float = 0.0,
    description: str | None = None,
    glidepath_years: float = 0.0,
    risky_store_name: str | None = None,
) -> None:
    """Add a one-time fixed acquisition (outflow) in exactly one step.

    `amount` is always a positive magnitude - it's negated internally
    regardless of the sign passed in, so a caller cannot accidentally invert
    the direction by pre-negating it. A one-time windfall (Sondereinnahme,
    e.g. an inheritance) is a positive cashflow, not a negative acquisition -
    use add_income_stream with start_step==end_step for that instead.

    If `glidepath_years > 0` and `risky_store_name` is provided, capital is
    gradually shifted from `risky_store_name` into `store_name` over the
    `glidepath_years` window preceding `step`.

    Both store names reference existing Stores and are validated up front
    (`risky_store_name` only when the glidepath actually uses it) - a typo'd
    name would otherwise create an effect the simulation silently never
    applies.
    """
    referenced_stores = [store_name]
    if glidepath_years > 0.0 and risky_store_name is not None:
        referenced_stores.append(risky_store_name)
    plan.validate_store_names(referenced_stores)

    if glidepath_years > 0.0 and risky_store_name is not None:
        glidepath_steps = round(glidepath_years * plan.timeline.steps_per_year)
        glidepath_start_step = max(0, step - glidepath_steps)
        add_flexible_acquisition(
            plan=plan,
            name=name,
            amount=amount,
            target_step=step,
            tolerance_steps=0,
            risky_store_name=risky_store_name,
            safe_store_name=store_name,
            glidepath_start_step=glidepath_start_step,
            inflation_rate=inflation_rate,
            description=description,
        )
        return

    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=-abs(amount),
        growth_rate=inflation_rate,
        start_step=step,
        end_step=step,
        description=description,
    )
    plan.effects.append(effect)


class FlexibleAcquisitionParameters(BaseModel):
    """Configuration for the `flexible_acquisition` computed effect.

    Excludes `triggered_step`: that's run-scoped mutable state (set once the
    acquisition fires), not configuration, so it's read/written directly on
    the raw parameters dict rather than through this model.
    """

    target_step: int
    tolerance_steps: int
    amount: float
    inflation_rate: float = 0.0
    risky_store_name: str
    safe_store_name: str
    glidepath_start_step: int


@register_computed_effect("flexible_acquisition")
def flexible_acquisition_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    """Computed effect implementing flexible acquisition with trigger and glidepath logic."""
    params = FlexibleAcquisitionParameters.model_validate(parameters)
    target_step = params.target_step
    tolerance_steps = params.tolerance_steps
    risky_store_name = params.risky_store_name
    safe_store_name = params.safe_store_name
    glidepath_start_step = params.glidepath_start_step

    # If already triggered, do nothing
    if parameters.get("triggered_step") is not None:
        return

    amount_inflated = params.amount * ((1.0 + params.inflation_rate) ** step)
    trigger_start_step = target_step - tolerance_steps
    trigger_end_step = target_step + tolerance_steps

    # 1. Glidepath Shifting (rebalance from risky to safe)
    if step >= glidepath_start_step:
        if step < trigger_start_step:
            denominator = trigger_start_step - glidepath_start_step
            fraction = (step - glidepath_start_step) / denominator if denominator > 0 else 1.0
            safe_target = amount_inflated * fraction
        else:
            safe_target = amount_inflated

        current_safe = balances.get(safe_store_name, 0.0)
        if current_safe < safe_target:
            shift = min(safe_target - current_safe, balances.get(risky_store_name, 0.0))
            if shift > 0.0:
                balances[risky_store_name] = balances.get(risky_store_name, 0.0) - shift
                balances[safe_store_name] = current_safe + shift

    # 2. Trigger Evaluation
    if trigger_start_step <= step <= trigger_end_step:
        actual_total = balances.get(safe_store_name, 0.0) + balances.get(risky_store_name, 0.0)
        ref_value = amount_inflated * (step / target_step) if target_step > 0 else amount_inflated

        if actual_total >= ref_value or step == trigger_end_step:
            # Trigger the acquisition!
            parameters["triggered_step"] = step
            current_safe = balances.get(safe_store_name, 0.0)

            if current_safe >= amount_inflated:
                balances[safe_store_name] = current_safe - amount_inflated
            else:
                remaining = amount_inflated - current_safe
                balances[safe_store_name] = 0.0
                balances[risky_store_name] = balances.get(risky_store_name, 0.0) - remaining


def add_flexible_acquisition(
    plan: Plan,
    name: str,
    amount: float,
    target_step: int,
    tolerance_steps: int,
    risky_store_name: str,
    safe_store_name: str,
    glidepath_start_step: int,
    inflation_rate: float = 0.0,
    description: str | None = None,
) -> None:
    """Add a computed flexible acquisition effect to the plan.

    `amount` is always a positive magnitude - it's normalized internally
    regardless of the sign passed in, matching add_fixed_acquisition's
    convention (a flexible acquisition is always an outflow by definition).

    `risky_store_name` and `safe_store_name` reference existing Stores and
    are validated up front - a typo'd name would otherwise create an effect
    that silently shifts nothing.
    """
    plan.validate_store_names([risky_store_name, safe_store_name])
    params = FlexibleAcquisitionParameters(
        target_step=target_step,
        tolerance_steps=tolerance_steps,
        amount=abs(amount),
        inflation_rate=inflation_rate,
        risky_store_name=risky_store_name,
        safe_store_name=safe_store_name,
        glidepath_start_step=glidepath_start_step,
    )
    effect = ComputedEffect(
        name=name,
        function_name="flexible_acquisition",
        parameters=params.model_dump(),
        description=description,
    )
    plan.effects.append(effect)
