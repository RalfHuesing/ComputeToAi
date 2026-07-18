"""Statutory pension (gesetzliche Rente) including Rentenabschlag/-zuschlag.

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/05-Feature-Finanzen-Parameter.md.
"""

from compute_to_ai.engine.effect import GrowingFixedEffect
from compute_to_ai.engine.plan import Plan


def calculate_pension_adjustment_factor(
    regular_retirement_step: int,
    actual_retirement_step: int,
    early_reduction_rate_per_month: float = 0.003,
    early_reduction_cap: float = 0.144,
    late_bonus_rate_per_month: float = 0.005,
) -> float:
    """Calculate the one-time Rentenabschlag/-zuschlag adjustment factor.

    One step is one year (12 months), matching the yearly simulation step
    (Docs/04-Feature-Finanzen-Methodik.md). Claiming early reduces the
    pension by `early_reduction_rate_per_month` per month, capped at
    `early_reduction_cap`; deferring increases it by
    `late_bonus_rate_per_month` per month, uncapped (Docs/05, sourced in
    Docs/09-Quellen.md).
    """
    months_early = max(0, regular_retirement_step - actual_retirement_step) * 12
    months_late = max(0, actual_retirement_step - regular_retirement_step) * 12
    reduction = min(early_reduction_cap, months_early * early_reduction_rate_per_month)
    bonus = months_late * late_bonus_rate_per_month
    return 1.0 - reduction + bonus


def add_statutory_pension(
    plan: Plan,
    name: str,
    store_name: str,
    monthly_amount_at_regular_retirement_age: float,
    regular_retirement_step: int,
    actual_retirement_step: int,
    annual_increase_rate: float = 0.0,
    early_reduction_rate_per_month: float = 0.003,
    early_reduction_cap: float = 0.144,
    late_bonus_rate_per_month: float = 0.005,
    active_phases: list[str] | None = None,
    end_step: int | None = None,
) -> None:
    """Add the statutory pension (gesetzliche Rente) as a growing income effect.

    The Rentenabschlag/-zuschlag is applied once, at construction time, as an
    adjustment to the pension's base amount - not as a separate mechanism.
    Statutory pension is otherwise the same building block as any other
    income stream (see Docs/01-Kern-Domaenenmodell.md, "Effekt-Arten"): a
    GrowingFixedEffect, only the base amount and start step differ.
    """
    adjustment_factor = calculate_pension_adjustment_factor(
        regular_retirement_step=regular_retirement_step,
        actual_retirement_step=actual_retirement_step,
        early_reduction_rate_per_month=early_reduction_rate_per_month,
        early_reduction_cap=early_reduction_cap,
        late_bonus_rate_per_month=late_bonus_rate_per_month,
    )
    annual_amount = monthly_amount_at_regular_retirement_age * 12.0 * adjustment_factor

    effect = GrowingFixedEffect(
        name=name,
        store_name=store_name,
        amount_per_step=annual_amount,
        growth_rate=annual_increase_rate,
        active_phases=active_phases,
        start_step=actual_retirement_step,
        end_step=end_step,
    )
    plan.effects.append(effect)
