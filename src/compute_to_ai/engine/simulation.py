"""SimulationRun execution - see Docs/01-Kern-Domaenenmodell.md.

A single deterministic pass over the Timeline, applying each Effect to its
Store at every step.
"""

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import SimulationResult


def run_simulation(plan: Plan) -> SimulationResult:
    balances = {store.name: store.balance for store in plan.stores}
    time_series: list[dict[str, float]] = []

    for _ in range(plan.timeline.step_count):
        for effect in plan.effects:
            balances[effect.store_name] += effect.amount_per_step
        time_series.append(dict(balances))

    return SimulationResult(final_balances=balances, time_series=time_series)
