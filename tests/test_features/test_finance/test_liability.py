import pytest

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.simulation import run_simulation
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline
from compute_to_ai.features.finance.liability import ScheduledExtraPayment, add_liability


def test_loan_amortization_without_extra_payments() -> None:
    plan = Plan(
        name="regular-loan-test",
        timeline=Timeline(step_count=4),
        stores=[Store(name="cash", balance=1000.0)],
    )

    # Principal: 500, interest rate: 10% per step, payment: 200 per step
    add_liability(
        plan=plan,
        name="Loan",
        liability_store_name="loan_store",
        cash_store_name="cash",
        principal=500.0,
        interest_rate=0.10,
        payment=200.0,
    )

    result = run_simulation(plan)

    # Step-by-step trace:
    # Step 0:
    # Interest: 500 * 0.10 is 50 -> loan becomes 550
    # Payment: -200 -> loan becomes 350, cash becomes 800
    #
    # Step 1:
    # Interest: 350 * 0.10 is 35 -> loan becomes 385
    # Payment: -200 -> loan becomes 185, cash becomes 600
    #
    # Step 2:
    # Interest: 185 * 0.10 is 18.5 -> loan becomes 203.5
    # Payment: -200 -> loan becomes 3.5, cash becomes 400
    #
    # Step 3:
    # Interest: 3.5 * 0.10 is 0.35 -> loan becomes 3.85
    # Payment: -200 -> loan goes to -196.15 in Phase 1, cash goes to 200.
    # Phase 2: computed manager detects overpayment.
    # Refund is 196.15. Cash becomes 200 + 196.15 is 396.15.
    # Loan is set to exactly 0.0.
    assert pytest.approx(result.final_balances["loan_store"]) == 0.0
    assert pytest.approx(result.final_balances["cash"]) == 396.15


def test_loan_with_scheduled_extra_payments() -> None:
    plan = Plan(
        name="scheduled-extra-payment-test",
        timeline=Timeline(step_count=3),
        stores=[Store(name="cash", balance=1000.0)],
    )

    # Scheduled extra payment of 100.0 at step 1
    extra_payments = [ScheduledExtraPayment(step=1, amount=100.0)]

    add_liability(
        plan=plan,
        name="Loan",
        liability_store_name="loan_store",
        cash_store_name="cash",
        principal=500.0,
        interest_rate=0.10,
        payment=200.0,
        extra_payments=extra_payments,
    )

    result = run_simulation(plan)

    # Step 0:
    # End of step 0: loan is 350, cash is 800 (same as regular)
    #
    # Step 1:
    # Phase 1: loan becomes 385 - 200 is 185, cash becomes 600
    # Phase 2: extra payment of 100 applied.
    # Cash becomes 500, loan becomes 85.
    #
    # Step 2:
    # Phase 1:
    # Interest: 85 * 0.10 is 8.5 -> loan becomes 93.5
    # Payment: -200 -> loan goes to -106.5 in Phase 1, cash goes to 300.
    # Phase 2: computed manager detects overpayment.
    # Refund is 106.5. Cash becomes 300 + 106.5 is 406.5.
    # Loan is set to exactly 0.0. (Paid off in step 2 instead of 3).
    assert pytest.approx(result.final_balances["loan_store"]) == 0.0
    assert pytest.approx(result.final_balances["cash"]) == 406.5


def test_loan_with_threshold_extra_payments() -> None:
    plan = Plan(
        name="threshold-extra-payment-test",
        timeline=Timeline(step_count=2),
        stores=[Store(name="cash", balance=1000.0)],
    )

    # Threshold parameters:
    # Extra payment of 50.0 is made if interest_rate >= 8% (0.08) and cash > 700.0
    add_liability(
        plan=plan,
        name="Loan",
        liability_store_name="loan_store",
        cash_store_name="cash",
        principal=500.0,
        interest_rate=0.10,
        payment=200.0,
        extra_payment_amount=50.0,
        extra_payment_threshold_rate=0.08,
        extra_payment_min_cash=700.0,
    )

    result = run_simulation(plan)

    # Step 0:
    # Phase 1: loan becomes 550 - 200 is 350. cash becomes 800.
    # Phase 2: interest_rate (10%) >= 8% and cash (800) > 700.
    # Extra payment amount is min(50, 800 - 700) is 50.
    # Cash becomes 750, loan becomes 300.
    #
    # Step 1:
    # Phase 1:
    # Interest: 300 * 0.10 is 30 -> loan becomes 330.
    # Payment: -200 -> loan becomes 130, cash becomes 550.
    # Phase 2: cash (550) <= 700. No extra payment is made.
    # End of step 1: loan is 130, cash is 550.
    assert pytest.approx(result.final_balances["loan_store"]) == 130.0
    assert pytest.approx(result.final_balances["cash"]) == 550.0
