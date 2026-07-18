"""SimulationRun execution - see Docs/01-Kern-Domaenenmodell.md.

Milestone 1 scope only: a single deterministic pass over the Timeline
applying fixed Effects. Monte Carlo (repeated stochastic runs) arrives with
Milestone 2 once a stochastic Effect kind exists (see Docs/10-Roadmap.md).
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
