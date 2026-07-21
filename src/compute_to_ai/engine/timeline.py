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
    description: str | None = None


class Timeline(BaseModel):
    """A sequence of discrete steps a Plan is simulated over.

    The engine has no notion of what a step represents (a month, a day, a
    year) - that meaning comes from whichever feature module configures the
    Effects (see Docs/02-Architektur-und-MCP.md, "Kein eigenes Frontend").
    `steps_per_year` makes that meaning explicit wherever a feature module
    needs to convert a calendar-based frequency (e.g. "monthly") into a step
    count - it defaults to 12 (one step per month); a Plan built on annual
    steps sets it to 1.
    """

    step_count: int = Field(gt=0)
    steps_per_year: int = Field(default=12, gt=0)
