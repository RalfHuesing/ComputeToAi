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

FREQUENCY_MAP: dict[str, int] = {
    "monthly": 1,
    "quarterly": 3,
    "yearly": 12,
    "annual": 12,
}


def parse_frequency_to_interval(
    frequency: str = "monthly",
    interval_years: int | None = None,
) -> int:
    """Parse frequency string and optional interval_years into step count (months)."""
    freq = frequency.lower()
    if freq in FREQUENCY_MAP:
        return FREQUENCY_MAP[freq]
    if freq == "every_n_years":
        if interval_years is None or interval_years < 1:
            msg = "interval_years must be at least 1 when frequency is 'every_n_years'"
            raise ValueError(msg)
        return interval_years * 12
    supported = [*FREQUENCY_MAP.keys(), "every_n_years"]
    msg = f"Unknown frequency: {frequency!r}. Supported values: {supported}"
    raise ValueError(msg)


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
    """Add a growing fixed income stream (positive cashflow) to the plan."""
    plan.validate_active_phases(active_phases)
    interval_steps = parse_frequency_to_interval(frequency, interval_years)
    if first_occurrence_year is not None:
        first_occurrence_step = round(first_occurrence_year * 12)

    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=amount,
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
    """Add an inflation-adjusted expense (negative cashflow) to the plan."""
    plan.validate_active_phases(active_phases)
    interval_steps = parse_frequency_to_interval(frequency, interval_years)
    if first_occurrence_year is not None:
        first_occurrence_step = round(first_occurrence_year * 12)

    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=-amount,
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
    """
    if glidepath_years > 0.0 and risky_store_name is not None:
        glidepath_steps = round(glidepath_years * 12)
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
    """
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
