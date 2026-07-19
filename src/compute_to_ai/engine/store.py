"""Store and Lot models.

See Docs/01-Kern-Domaenenmodell.md and Docs/11-Code-Standards-und-Projektstruktur.md.
"""

from pydantic import BaseModel


class Lot(BaseModel):
    """A specific unit of currency/asset purchased at a specific time.

    Required for rule-version-aware FIFO asset selling. `metadata` is a generic
    extension point for feature-specific per-lot bookkeeping (e.g. a tax
    building block tracking already-taxed gains); the engine assigns it no
    meaning and only ever splits it proportionally on partial withdrawal.
    """

    quantity: float
    created_step: int
    rule_version: str | None = None
    cost_basis: float = 0.0
    metadata: dict[str, float] = {}


class Store(BaseModel):
    """A balance that changes over a Timeline through Effects.

    Optionally tracks detailed Lots for FIFO valuation and taxation.
    """

    name: str
    balance: float = 0.0
    lots: list[Lot] = []
    withdrawn_lots_this_step: list[Lot] = []
    description: str | None = None

    def add_amount(
        self,
        amount: float,
        step: int,
        rule_version: str | None = None,
        cost_basis: float | None = None,
        track_lots: bool = False,
    ) -> None:
        """Add an amount to the store, creating a new Lot if lot tracking is active."""
        has_cost_basis = cost_basis is not None and cost_basis > 0.0
        if track_lots or self.lots or rule_version is not None or has_cost_basis:
            actual_cost = amount if cost_basis is None or cost_basis == 0.0 else cost_basis
            self.lots.append(
                Lot(
                    quantity=amount,
                    created_step=step,
                    rule_version=rule_version,
                    cost_basis=actual_cost,
                )
            )
            self.balance = sum(lot.quantity for lot in self.lots)
        else:
            self.balance += amount

    def withdraw_amount(self, amount: float) -> list[Lot]:
        """Withdraw an amount from the store, consuming lots in FIFO order if active."""
        if self.lots:
            consumed: list[Lot] = []
            remaining = amount
            while remaining > 0 and self.lots:
                lot = self.lots[0]
                if lot.quantity <= remaining:
                    consumed.append(lot)
                    remaining -= lot.quantity
                    self.lots.pop(0)
                else:
                    # Partial consumption: copy lot with consumed quantity
                    fraction = remaining / lot.quantity
                    consumed_cost = lot.cost_basis * fraction
                    consumed_metadata = {k: v * fraction for k, v in lot.metadata.items()}

                    consumed.append(
                        Lot(
                            quantity=remaining,
                            created_step=lot.created_step,
                            rule_version=lot.rule_version,
                            cost_basis=consumed_cost,
                            metadata=consumed_metadata,
                        )
                    )
                    lot.quantity -= remaining
                    lot.cost_basis -= consumed_cost
                    lot.metadata = {
                        k: v - consumed_metadata[k] for k, v in lot.metadata.items()
                    }
                    remaining = 0.0
            self.balance = sum(lot.quantity for lot in self.lots)
            self.withdrawn_lots_this_step.extend(consumed)
            return consumed

        self.balance -= amount
        return []

    def apply_percentage_growth(self, rate: float) -> None:
        """Multiply the balance and lot quantities by (1 + rate)."""
        factor = 1.0 + rate
        if self.lots:
            for lot in self.lots:
                lot.quantity *= factor
            self.balance = sum(lot.quantity for lot in self.lots)
        else:
            self.balance *= factor
