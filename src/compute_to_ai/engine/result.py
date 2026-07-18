"""SimulationResult - see Docs/01-Kern-Domaenenmodell.md."""

from pydantic import BaseModel


class SimulationResult(BaseModel):
    """Outcome of one SimulationRun: final balances, optional time series."""

    final_balances: dict[str, float]
    time_series: list[dict[str, float]] = []
