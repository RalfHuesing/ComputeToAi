"""Timeline - see Docs/01-Kern-Domaenenmodell.md."""

from pydantic import BaseModel, Field


class Timeline(BaseModel):
    """A sequence of discrete steps a Plan is simulated over.

    The engine has no notion of what a step represents (a month, a day, a
    year) - that meaning comes from whichever feature module configures the
    Effects (see Docs/02-Architektur-und-MCP.md, "Kein eigenes Frontend").
    """

    step_count: int = Field(gt=0)
