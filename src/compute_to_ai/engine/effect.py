"""Effect - see Docs/01-Kern-Domaenenmodell.md."""

from pydantic import BaseModel


class FixedEffect(BaseModel):
    """A constant amount applied to a Store at every Timeline step.

    The only Effect kind in Milestone 1 (see Docs/10-Roadmap.md). A shared
    Effect base and the Component/Baustein catalog arrive with Milestone 2,
    once a second Effect kind actually exists (Rule of Three, see
    Docs/11-Code-Standards-und-Projektstruktur.md).
    """

    store_name: str
    amount_per_step: float
