"""Plan - see Docs/01-Kern-Domaenenmodell.md."""

from pydantic import BaseModel

from compute_to_ai.engine.effect import FixedEffect
from compute_to_ai.engine.store import Store
from compute_to_ai.engine.timeline import Timeline

CURRENT_SCHEMA_VERSION = 1


class Plan(BaseModel):
    """A container of Stores, Effects and a Timeline that can be simulated.

    Carries a schema_version from the start so a persisted plan file can
    evolve without an older file being misread by a newer server version.
    """

    schema_version: int = CURRENT_SCHEMA_VERSION
    name: str
    timeline: Timeline
    stores: list[Store] = []
    effects: list[FixedEffect] = []

    def store(self, name: str) -> Store:
        for store in self.stores:
            if store.name == name:
                return store
        msg = f"no store named {name!r} in plan {self.name!r}"
        raise KeyError(msg)
