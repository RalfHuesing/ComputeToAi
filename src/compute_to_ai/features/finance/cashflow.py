"""Financial cashflow components (income, expense, acquisitions).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

from compute_to_ai.engine.effect import (
    ComputedEffect,
    GrowingFixedEffect,
    register_computed_effect,
)
from compute_to_ai.engine.plan import Plan


def add_income_stream(
    plan: Plan,
    name: str,
    store_name: str,
    amount: float,
    growth_rate: float = 0.0,
    active_phases: list[str] | None = None,
    start_step: int | None = None,
    end_step: int | None = None,
) -> None:
    """Add a growing fixed income stream (positive cashflow) to the plan."""
    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=amount,
        growth_rate=growth_rate,
        active_phases=active_phases,
        start_step=start_step,
        end_step=end_step,
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
) -> None:
    """Add an inflation-adjusted expense (negative cashflow) to the plan."""
    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=-amount,
        growth_rate=inflation_rate,
        active_phases=active_phases,
        start_step=start_step,
        end_step=end_step,
    )
    plan.effects.append(effect)


def add_fixed_acquisition(
    plan: Plan,
    name: str,
    store_name: str,
    amount: float,
    step: int,
    inflation_rate: float = 0.0,
) -> None:
    """Add a one-time fixed acquisition (negative cashflow) in exactly one step."""
    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=-amount,
        growth_rate=inflation_rate,
        start_step=step,
        end_step=step,
    )
    plan.effects.append(effect)


@register_computed_effect("flexible_acquisition")
def flexible_acquisition_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    """Computed effect implementing flexible acquisition with trigger and glidepath logic."""
    target_step = int(parameters["target_step"])
    tolerance_steps = int(parameters["tolerance_steps"])
    amount = float(parameters["amount"])
    inflation_rate = float(parameters.get("inflation_rate", 0.0))
    risky_store_name = str(parameters["risky_store_name"])
    safe_store_name = str(parameters["safe_store_name"])
    glidepath_start_step = int(parameters["glidepath_start_step"])

    # If already triggered, do nothing
    if parameters.get("triggered_step") is not None:
        return

    amount_inflated = amount * ((1.0 + inflation_rate) ** step)
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
) -> None:
    """Add a computed flexible acquisition effect to the plan."""
    effect = ComputedEffect(
        name=name,
        function_name="flexible_acquisition",
        parameters={
            "target_step": target_step,
            "tolerance_steps": tolerance_steps,
            "amount": amount,
            "inflation_rate": inflation_rate,
            "risky_store_name": risky_store_name,
            "safe_store_name": safe_store_name,
            "glidepath_start_step": glidepath_start_step,
        },
    )
    plan.effects.append(effect)
