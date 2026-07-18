"""Store - see Docs/01-Kern-Domaenenmodell.md."""

from pydantic import BaseModel


class Store(BaseModel):
    """A balance that changes over a Timeline through Effects."""

    name: str
    balance: float = 0.0
