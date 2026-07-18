"""Simulation result models.

See Docs/01-Kern-Domaenenmodell.md and Docs/11-Code-Standards-und-Projektstruktur.md.
"""

from pydantic import BaseModel


class SimulationResult(BaseModel):
    """Outcome of one SimulationRun.

    Includes final balances, optional time series, and optional ruin step.
    """

    final_balances: dict[str, float]
    time_series: list[dict[str, float]] = []
    ruin_step: int | None = None


class MonteCarloResult(BaseModel):
    """Outcome of a Monte-Carlo simulation containing aggregates across multiple runs."""

    num_runs: int
    ruin_probability: float
    ruin_step_distribution: dict[int, int]  # maps step -> count of ruins occurring at that step
    final_balances_percentiles: dict[str, dict[int, float]]  # store_name -> percentile_key -> value
    raw_final_balances: list[dict[str, float]] = []
