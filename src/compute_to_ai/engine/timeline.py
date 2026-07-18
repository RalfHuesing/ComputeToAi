"""Timeline and Phase models.

See Docs/01-Kern-Domaenenmodell.md and Docs/11-Code-Standards-und-Projektstruktur.md.
"""

from pydantic import BaseModel, Field


class Phase(BaseModel):
    """A named period of time with start and end step boundaries.

    Interval is half-open: [start_step, end_step) (inclusive start, exclusive end).
    """

    name: str
    start_step: int
    end_step: int


class Timeline(BaseModel):
    """A sequence of discrete steps a Plan is simulated over.

    The engine has no notion of what a step represents (a month, a day, a
    year) - that meaning comes from whichever feature module configures the
    Effects (see Docs/02-Architektur-und-MCP.md, "Kein eigenes Frontend").
    """

    step_count: int = Field(gt=0)
