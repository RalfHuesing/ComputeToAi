"""Store and Lot models.

See Docs/01-Kern-Domaenenmodell.md and Docs/11-Code-Standards-und-Projektstruktur.md.
"""

from pydantic import BaseModel


class Lot(BaseModel):
    """A specific unit of currency/asset purchased at a specific time.

    Required for tax-aware FIFO asset selling.
    """

    quantity: float
    created_step: int
    rule_version: str | None = None
    cost_basis: float = 0.0
    taxed_vorabpauschale: float = 0.0


class Store(BaseModel):
    """A balance that changes over a Timeline through Effects.

    Optionally tracks detailed Lots for FIFO valuation and taxation.
    """

    name: str
    balance: float = 0.0
    lots: list[Lot] = []

    def add_amount(
        self,
        amount: float,
        step: int,
        rule_version: str | None = None,
        cost_basis: float = 0.0,
        track_lots: bool = False,
    ) -> None:
        """Add an amount to the store, creating a new Lot if lot tracking is active."""
        if track_lots or self.lots or rule_version is not None or cost_basis > 0.0:
            self.lots.append(
                Lot(
                    quantity=amount,
                    created_step=step,
                    rule_version=rule_version,
                    cost_basis=cost_basis,
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
                    consumed_vorab = lot.taxed_vorabpauschale * fraction

                    consumed.append(
                        Lot(
                            quantity=remaining,
                            created_step=lot.created_step,
                            rule_version=lot.rule_version,
                            cost_basis=consumed_cost,
                            taxed_vorabpauschale=consumed_vorab,
                        )
                    )
                    lot.quantity -= remaining
                    lot.cost_basis -= consumed_cost
                    lot.taxed_vorabpauschale -= consumed_vorab
                    remaining = 0.0
            self.balance = sum(lot.quantity for lot in self.lots)
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
