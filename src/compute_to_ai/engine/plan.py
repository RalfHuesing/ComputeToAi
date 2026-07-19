"""Plan - see Docs/01-Kern-Domaenenmodell.md."""

from pydantic import BaseModel

from compute_to_ai.engine.effect import Effect
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Phase, Timeline

CURRENT_SCHEMA_VERSION = 1


class CorrelationGroup(BaseModel):
    """Configuration of a correlation relationship between multiple stochastic effects.

    Matches stores to their position in a symmetric correlation matrix.
    """

    matrix: list[list[float]]
    store_names: list[str]


class Plan(BaseModel):
    """A container of Stores, Effects, Phases, and a Timeline that can be simulated.

    Carries a schema_version from the start so a persisted plan file can
    evolve without an older file being misread by a newer server version.
    """

    schema_version: int = CURRENT_SCHEMA_VERSION
    name: str
    timeline: Timeline
    stores: list[Store] = []
    effects: list[Effect] = []
    phases: list[Phase] = []
    correlation_groups: dict[str, CorrelationGroup] = {}
    ruin_stores: list[str] = []
    ruin_threshold: float = 0.0
    description: str | None = None

    def store(self, name: str) -> Store:
        """Find a Store by its name or raise KeyError."""
        for store in self.stores:
            if store.name == name:
                return store
        msg = f"no store named {name!r} in plan {self.name!r}"
        raise KeyError(msg)

    def get_active_phase_name(self, step: int) -> str | None:
        """Return the name of the phase that is active at the given step, if any."""
        for phase in self.phases:
            if phase.start_step <= step < phase.end_step:
                return phase.name
        return None

    def validate_active_phases(self, active_phases: list[str] | None) -> None:
        """Raise ValueError if any name in active_phases is not a registered Phase.

        Without this, a typo'd phase name is accepted silently and the effect
        referencing it simply never activates (BaseEffect.is_active never
        matches), instead of failing at configuration time.
        """
        if active_phases is None:
            return
        known = {phase.name for phase in self.phases}
        unknown = [name for name in active_phases if name not in known]
        if unknown:
            msg = f"unknown phase name(s) {unknown!r} in plan {self.name!r}"
            raise ValueError(msg)
