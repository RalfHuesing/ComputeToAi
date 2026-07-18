"""Effect - see Docs/01-Kern-Domaenenmodell.md."""

from pydantic import BaseModel


class FixedEffect(BaseModel):
    """A constant amount applied to a Store at every Timeline step.

    No shared Effect base class exists because FixedEffect is the only
    kind so far (Rule of Three, see
    Docs/11-Code-Standards-und-Projektstruktur.md).
    """

    store_name: str
    amount_per_step: float
