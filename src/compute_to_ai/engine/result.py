"""Simulation result models.

See Docs/01-Kern-Domaenenmodell.md and Docs/11-Code-Standards-und-Projektstruktur.md.
"""

from typing import Any, Literal

from pydantic import BaseModel

LedgerEffectType = Literal[
    "growing_fixed", "percentage_growth", "correlated_return", "computed", "transfer"
]


class LedgerEntry(BaseModel):
    """One (Effect, Store) balance change at one step of an instrumented run.

    Populated only when a run explicitly opts into instrumentation (see
    Docs/01-Kern-Domaenenmodell.md, "Ledger"). The engine records which
    Effect changed which Store's balance by how much, without attaching any
    domain meaning (e.g. "income" vs. "expense") to that change - that
    classification is left to feature modules.

    For a `percentage_growth`/`correlated_return` effect sharing a Store
    with another growth effect in the same step, `delta` is that effect's
    linear share of the combined growth rate applied to the pre-step
    balance - an approximation, exact whenever (as is typical) only one
    growth effect targets a given Store.
    """

    step: int
    effect_name: str
    effect_type: LedgerEffectType
    function_name: str | None = None
    store_name: str
    delta: float


class ComputedEffectFinalState(BaseModel):
    """The post-run state of one ComputedEffect's run-scoped `parameters`.

    Surfaces mutable state a ComputedEffect wrote into its own `parameters`
    dict during a run (e.g. a one-time trigger flag) - state that would
    otherwise be discarded once the run-scoped effect clone is dropped after
    the run. Only populated for instrumented runs.
    """

    effect_name: str
    function_name: str
    parameters: dict[str, Any]


class SimulationResult(BaseModel):
    """Outcome of one SimulationRun.

    Includes final balances, optional time series, optional ruin step, and -
    only for instrumented runs - a per-step ledger and computed-effect final
    states (see Docs/01-Kern-Domaenenmodell.md, "Ledger").
    """

    final_balances: dict[str, float]
    time_series: list[dict[str, float]] = []
    ruin_step: int | None = None
    ruin_shortfall: float | None = None
    ledger: list[LedgerEntry] = []
    computed_effect_final_states: list[ComputedEffectFinalState] = []


class MonteCarloResult(BaseModel):
    """Outcome of a Monte-Carlo simulation containing aggregates across multiple runs."""

    num_runs: int
    ruin_probability: float
    ruin_step_distribution: dict[int, int]  # maps step -> count of ruins occurring at that step
    final_balances_percentiles: dict[str, dict[int, float]]  # store_name -> percentile_key -> value
    raw_final_balances: list[dict[str, float]] = []
    # percentile_key -> value, over runs that ruined; {} if none did
    ruin_shortfall_percentiles: dict[int, float] = {}


class PathAuditResult(BaseModel):
    """Instrumented per-step history for a few representative paths of a
    Monte-Carlo run (percentile matches plus the deterministic reference
    run), keyed by a free-form path label (e.g. "p50", "p10",
    "deterministic") - see Docs/01-Kern-Domaenenmodell.md, "Ledger".
    """

    num_runs: int
    paths: dict[str, SimulationResult]
