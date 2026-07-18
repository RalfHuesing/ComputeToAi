"""Financial liabilities and debt management (loans, amortization, Sondertilgung).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

from compute_to_ai.engine.effect import (
    ComputedEffect,
    GrowingFixedEffect,
    PercentageGrowthEffect,
    register_computed_effect,
)
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.store import Store


@register_computed_effect("liability_manager")
def liability_manager_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], step: int, parameters: dict[str, Any], _plan: Plan
) -> None:
    """Computed effect that reconciles overpayment refunds and applies Sondertilgungen."""
    liability_store = str(parameters["liability_store_name"])
    cash_store = str(parameters["cash_store_name"])
    payment = float(parameters["payment"])
    interest_rate = float(parameters["interest_rate"])

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
    extra_payments = parameters.get("extra_payments")
    if extra_payments is not None:
        for ep in extra_payments:
            if int(ep.get("step", -1)) == step:
                extra_amount += float(ep.get("amount", 0.0))

    # 2. Threshold-based
    threshold_rate = parameters.get("extra_payment_threshold_rate")
    if threshold_rate is not None and interest_rate >= float(threshold_rate):
        extra_payment_amount = float(parameters.get("extra_payment_amount", 0.0))
        min_cash = float(parameters.get("extra_payment_min_cash", 0.0))
        cash_avail = balances.get(cash_store, 0.0)
        if cash_avail > min_cash:
            extra_amount += min(extra_payment_amount, cash_avail - min_cash)

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
    extra_payments: list[dict[str, Any]] | None = None,
) -> None:
    """Add a liability to the plan with regular payments and optional extra payments."""
    # Ensure the liability store is registered
    store_exists = False
    for st in plan.stores:
        if st.name == liability_store_name:
            store_exists = True
            break
    if not store_exists:
        plan.stores.append(Store(name=liability_store_name, balance=principal))

    # Zins (PercentageGrowthEffect on liability store)
    plan.effects.append(
        PercentageGrowthEffect(
            name=f"{name} Zins",
            store_name=liability_store_name,
            growth_rate=interest_rate,
            start_step=start_step,
            end_step=end_step,
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
        )
    )

    # Computed manager to reconcile overpayments and handle Sondertilgungen
    plan.effects.append(
        ComputedEffect(
            name=f"{name} Manager",
            function_name="liability_manager",
            start_step=start_step,
            end_step=end_step,
            parameters={
                "liability_store_name": liability_store_name,
                "cash_store_name": cash_store_name,
                "payment": payment,
                "interest_rate": interest_rate,
                "extra_payment_amount": extra_payment_amount,
                "extra_payment_threshold_rate": extra_payment_threshold_rate,
                "extra_payment_min_cash": extra_payment_min_cash,
                "extra_payments": extra_payments,
            },
        )
    )
