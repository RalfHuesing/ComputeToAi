"""Position metadata and balance updates from live share prices.

See Docs/03-Feature-Finanzen-Domaenenmodell.md, "Position (ETF-/Fondsanteil,
Konto)", and Docs/04-Feature-Finanzen-Methodik.md.
"""

from datetime import date

from pydantic import BaseModel

from compute_to_ai.engine.store import Store

_PRE_2009_CUTOFF = date(2009, 1, 1)


class PositionMetadata(BaseModel):
    """ISIN/WKN, share count, and exchange backing one store's live-price tracking."""

    isin_or_wkn: str
    shares: float
    exchange: str
    last_updated: str


class PositionPriceUpdate(BaseModel):
    """One store successfully repriced by `finance_update_plan_prices`."""

    store_name: str
    old_balance: float
    new_balance: float
    price: float
    currency: str


class PriceUpdateResult(BaseModel):
    """Result of `finance_update_plan_prices`: which positions updated vs. were skipped.

    A position is skipped rather than aborting the whole run - one stale
    ISIN or one temporarily unreachable quote must not prevent every other
    position from being refreshed.
    """

    updated: list[PositionPriceUpdate] = []
    skipped: dict[str, str] = {}


class PositionRegistry(BaseModel):
    """All positions with live-price metadata in a plan, keyed by store name.

    A store absent from this registry stays purely manually maintained -
    metadata here is optional bookkeeping, not a requirement for every
    store that happens to represent a Position.
    """

    positions: dict[str, PositionMetadata] = {}


def set_position_balance(store: Store, shares: float, price: float, step: int = 0) -> None:
    """Initialize/replace a position's balance from a bare share count and price.

    Fully replaces any existing lots with a single fresh lot dated at `step`,
    with cost basis equal to today's market value - a bare share count alone
    carries no purchase-price history, so no historical gain can be
    recovered here (see Docs/03-Feature-Finanzen-Domaenenmodell.md,
    "Position (ETF-/Fondsanteil, Konto)"); an accurate lot history requires
    the transaction-history path instead.
    """
    store.lots = []
    store.withdrawn_lots_this_step = []
    store.balance = 0.0
    market_value = shares * price
    store.add_amount(market_value, step=step, cost_basis=market_value)


class PositionTransaction(BaseModel):
    """A single dated, priced share transaction backing a historical lot
    reconstruction (see `apply_transaction_history`).

    `shares` follows the same signed convention as `ShareTransaction` in
    `compute_to_ai.features.calculations.holdings` (positive = bought,
    negative = sold). `price` is the price per share paid/received at that
    transaction - required for buys, ignored for sells (a sell consumes
    existing lots FIFO and needs no price of its own).
    """

    date: date
    shares: float
    price: float | None = None


def apply_transaction_history(store: Store, transactions: list[PositionTransaction]) -> None:
    """Rebuild a position's lots from its full priced transaction history.

    Fully replaces the store's current lots (same "replace, don't
    accumulate" semantics as `set_position_balance`), then replays
    `transactions` in chronological order: each buy creates a new lot at its
    own cost basis, each sell consumes existing lots FIFO via
    `Store.withdraw_amount`.

    Every replayed lot is created at `step=0` regardless of its real
    calendar date. Steps model a forward simulation starting today - step 0
    is "before the simulation begins", the natural step for anything that
    already happened in the past. Chronological order is preserved by the
    order lots are replayed in (sorted by `date`), not by the step number
    they're tagged with. Bestandsschutz (protection for pre-2009 holdings,
    see Docs/03-Feature-Finanzen-Domaenenmodell.md, "Besteuerung") is decided
    purely by each lot's `rule_version`, set here from the transaction date,
    never from `created_step`.
    """
    store.lots = []
    store.withdrawn_lots_this_step = []
    store.balance = 0.0

    for transaction in sorted(transactions, key=lambda t: t.date):
        if transaction.shares > 0:
            if transaction.price is None or transaction.price <= 0.0:
                msg = (
                    f"buy transaction on {transaction.date} needs a positive price "
                    "(price paid per share)"
                )
                raise ValueError(msg)
            cost_basis = transaction.shares * transaction.price
            rule_version = "pre_2009" if transaction.date < _PRE_2009_CUTOFF else None
            store.add_amount(
                cost_basis, step=0, cost_basis=cost_basis, rule_version=rule_version
            )
        elif transaction.shares < 0:
            store.withdraw_amount(-transaction.shares)


def apply_price_update(store: Store, shares: float, new_price: float) -> None:
    """Update a position's balance for a new market price of the same holding.

    Unlike `set_position_balance`, this is a market move on an existing
    holding, not a new purchase: it scales lot quantities via
    `Store.apply_percentage_growth` so cost basis is preserved (see
    Docs/04-Feature-Finanzen-Methodik.md, "Positions-Rebalancing innerhalb
    einer Anlageklasse"). Falls back to `set_position_balance` if the store
    has no balance yet, since a growth rate relative to zero is undefined.
    """
    if store.balance <= 0.0:
        set_position_balance(store, shares, new_price)
        return

    rate = (shares * new_price) / store.balance - 1.0
    store.apply_percentage_growth(rate)
