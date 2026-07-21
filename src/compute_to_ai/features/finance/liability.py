"""Financial liabilities and debt management (loans, amortization, Sondertilgung).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

from pydantic import BaseModel

from compute_to_ai.engine.effect import (
    ComputedEffect,
    GrowingFixedEffect,
    PercentageGrowthEffect,
    register_computed_effect,
)
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.store import Store


class ScheduledExtraPayment(BaseModel):
    """A one-time extra payment (Sondertilgung) due at a specific step."""

    step: int
    amount: float


class LiabilityManagerParameters(BaseModel):
    """Parameters for the `liability_manager` computed effect.

    Both `add_liability` (writer) and `liability_manager_func` (reader)
    validate through this single model instead of matching dict-key strings
    by convention, so a typo becomes a validation error instead of a
    silently ignored default.
    """

    liability_store_name: str
    cash_store_name: str
    payment: float
    interest_rate: float
    extra_payments: list[ScheduledExtraPayment] = []
    extra_payment_threshold_rate: float | None = None
    extra_payment_amount: float = 0.0
    extra_payment_min_cash: float = 0.0


@register_computed_effect("liability_manager")
def liability_manager_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    """Computed effect that reconciles overpayment refunds and applies Sondertilgungen."""
    params = LiabilityManagerParameters.model_validate(parameters)
    liability_store = params.liability_store_name
    cash_store = params.cash_store_name
    payment = params.payment
    interest_rate = params.interest_rate

    l_phase1 = balances.get(liability_store, 0.0)

    # Calculate starting balance of this step before interest and payment
    l_start = (l_phase1 + payment) / (1.0 + interest_rate)

    if l_start <= 0.001:
        # Already fully paid off. Refund the payment to cash, set liability to 0
        balances[cash_store] = balances.get(cash_store, 0.0) + payment
        balances[liability_store] = 0.0
        return

    l_before_payment = l_start * (1.0 + interest_rate)

    # If the balance before payment is less than the scheduled payment, we overpaid
    if l_before_payment < payment:
        overpaid = payment - l_before_payment
        balances[cash_store] = balances.get(cash_store, 0.0) + overpaid
        balances[liability_store] = 0.0
        return

    # Regular payment applied cleanly. Calculate balance after payment
    l_after_payment = l_before_payment - payment

    # Determine if an extra payment is scheduled or triggered
    extra_amount = 0.0

    # 1. Scheduled list
    for ep in params.extra_payments:
        if ep.step == step:
            extra_amount += ep.amount

    # 2. Threshold-based
    if (
        params.extra_payment_threshold_rate is not None
        and interest_rate >= params.extra_payment_threshold_rate
    ):
        cash_avail = balances.get(cash_store, 0.0)
        if cash_avail > params.extra_payment_min_cash:
            extra_amount += min(
                params.extra_payment_amount, cash_avail - params.extra_payment_min_cash
            )

    # Apply extra payment
    if extra_amount > 0.0:
        actual_extra = min(extra_amount, l_after_payment)
        actual_extra = min(actual_extra, balances.get(cash_store, 0.0))
        if actual_extra > 0.0:
            balances[cash_store] = balances.get(cash_store, 0.0) - actual_extra
            balances[liability_store] = l_after_payment - actual_extra


def add_liability(
    plan: Plan,
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
) -> None:
    """Add a liability to the plan with regular payments and optional extra payments.

    `cash_store_name` references an existing Store and is validated up front
    (a typo'd name would otherwise create a phantom store the payments drain
    unnoticed); `liability_store_name` is this liability's own store and is
    auto-created if missing.
    """
    plan.validate_store_names([cash_store_name])

    # Ensure the liability store is registered
    store_exists = False
    for st in plan.stores:
        if st.name == liability_store_name:
            store_exists = True
            break
    if not store_exists:
        plan.stores.append(
            Store(name=liability_store_name, balance=principal, description=description)
        )

    # Zins (PercentageGrowthEffect on liability store)
    plan.effects.append(
        PercentageGrowthEffect(
            name=f"{name} Zins",
            store_names=[liability_store_name],
            growth_rate=interest_rate,
            start_step=start_step,
            end_step=end_step,
            description=description,
        )
    )

    # Tilgung (negative GrowingFixedEffect on liability store)
    plan.effects.append(
        GrowingFixedEffect(
            name=f"{name} Tilgung",
            store_name=liability_store_name,
            amount_per_step=-payment,
            growth_rate=0.0,
            start_step=start_step,
            end_step=end_step,
            description=description,
        )
    )

    # Cash Rate (negative GrowingFixedEffect on cash store)
    plan.effects.append(
        GrowingFixedEffect(
            name=f"{name} Rate",
            store_name=cash_store_name,
            amount_per_step=-payment,
            growth_rate=0.0,
            start_step=start_step,
            end_step=end_step,
            description=description,
        )
    )

    # Computed manager to reconcile overpayments and handle Sondertilgungen
    params = LiabilityManagerParameters(
        liability_store_name=liability_store_name,
        cash_store_name=cash_store_name,
        payment=payment,
        interest_rate=interest_rate,
        extra_payment_amount=extra_payment_amount,
        extra_payment_threshold_rate=extra_payment_threshold_rate,
        extra_payment_min_cash=extra_payment_min_cash,
        extra_payments=extra_payments or [],
    )
    plan.effects.append(
        ComputedEffect(
            name=f"{name} Manager",
            function_name="liability_manager",
            start_step=start_step,
            end_step=end_step,
            parameters=params.model_dump(),
            description=description,
        )
    )
