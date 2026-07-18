"""Store - see Docs/01-Kern-Domaenenmodell.md."""

from pydantic import BaseModel


class Store(BaseModel):
    """A balance that changes over a Timeline through Effects.

    Lot semantics (dated sub-balances, needed for tax purposes) arrive with
    Milestone 2 (see Docs/10-Roadmap.md); Milestone 1 only needs a single
    running balance.
    """

    name: str
    balance: float = 0.0
