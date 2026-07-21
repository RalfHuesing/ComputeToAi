"""Position metadata and balance updates from live share prices.

See Docs/03-Feature-Finanzen-Domaenenmodell.md, "Position (ETF-/Fondsanteil,
Konto)", and Docs/04-Feature-Finanzen-Methodik.md.
"""

from datetime import date
from typing import Any

from pydantic import BaseModel

from compute_to_ai.engine.effect import ComputedEffect, CorrelatedReturnEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.store import Store

_PRE_2009_CUTOFF = date(2009, 1, 1)


class PositionMetadata(BaseModel):
    """ISIN/WKN, share count, and exchange backing one store's live-price tracking."""

    isin_or_wkn: str
    shares: float
    exchange: str
    last_updated: str
    asset_type: str = "equity_fund"


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
    transaction - required for both directions: a buy needs it to record the
    lot's cost basis, and a sell needs it too, since a Store's Lots are
    money-denominated (`Lot.quantity` tracks a Euro value, not a raw share
    count, see `compute_to_ai.engine.store`) - withdrawing the bare share
    count instead of `shares * price` would consume the wrong fraction of
    the FIFO queue.
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
        if transaction.price is None or transaction.price <= 0.0:
            direction = "buy" if transaction.shares > 0 else "sell"
            msg = (
                f"{direction} transaction on {transaction.date} needs a positive price "
                "(Lots are money-denominated, see apply_transaction_history)"
            )
            raise ValueError(msg)

        if transaction.shares > 0:
            cost_basis = transaction.shares * transaction.price
            rule_version = "pre_2009" if transaction.date < _PRE_2009_CUTOFF else None
            store.add_amount(cost_basis, step=0, cost_basis=cost_basis, rule_version=rule_version)
        elif transaction.shares < 0:
            store.withdraw_amount(-transaction.shares * transaction.price)


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


def find_asset_class_effect(plan: Plan, asset_class_store_name: str) -> CorrelatedReturnEffect:
    """Find the CorrelatedReturnEffect an asset class's store belongs to, or raise ValueError."""
    for effect in plan.effects:
        if (
            isinstance(effect, CorrelatedReturnEffect)
            and asset_class_store_name in effect.store_names
        ):
            return effect
    msg = (
        f"no asset class containing store {asset_class_store_name!r} in plan {plan.name!r}; "
        "create it first with finance_add_asset_class"
    )
    raise ValueError(msg)


def find_positions_rebalancing_effect(plan: Plan, store_names: set[str]) -> ComputedEffect | None:
    """Find the positions_rebalancing ComputedEffect governing a set of position stores, if any.

    This effect type does not exist yet, so this always returns None today -
    written defensively (matched purely by `parameters`, no import of a
    not-yet-existing module) so `list_positions`/`remove_position` degrade
    gracefully in the meantime and need no changes once it is added.
    """
    for effect in plan.effects:
        if (
            isinstance(effect, ComputedEffect)
            and effect.function_name == "positions_rebalancing"
            and set(effect.parameters.get("store_names", [])) == store_names
        ):
            return effect
    return None


def add_position(
    plan: Plan,
    asset_class_store_name: str,
    store_name: str,
    description: str | None = None,
) -> None:
    """Add a new, still-unvalued position (store) to an existing asset class.

    Only creates the store and links it into the asset class's shared
    CorrelatedReturnEffect - it starts out at a zero balance. Follow up
    with `set_position_balance`/`apply_transaction_history` (or their
    finance_set_asset_shares/finance_set_position_from_transactions MCP
    wrappers) to actually value it, and (once available) a tool to mark it
    active for savings-rate priority.
    """
    effect = find_asset_class_effect(plan, asset_class_store_name)

    if store_name in {store.name for store in plan.stores}:
        msg = f"a store named {store_name!r} already exists in plan {plan.name!r}"
        raise ValueError(msg)
    if store_name in effect.store_names:
        msg = (
            f"store {store_name!r} is already a position of asset class {asset_class_store_name!r}"
        )
        raise ValueError(msg)

    plan.stores.append(Store(name=store_name, description=description))
    effect.store_names.append(store_name)


def list_positions(plan: Plan, asset_class_store_name: str) -> dict[str, Any]:
    """List every position (store) of one asset class with its current balance.

    The `active_store_name`/`sell_threshold` entries surface the position
    currently marked active for savings-rate priority and its configured
    sell threshold, if a positions-rebalancing effect for this asset class
    exists yet - both are `None` until that effect type is added (see
    `find_positions_rebalancing_effect`).
    """
    effect = find_asset_class_effect(plan, asset_class_store_name)
    positions = [
        {"store_name": name, "balance": plan.store(name).balance} for name in effect.store_names
    ]

    rebalancing_effect = find_positions_rebalancing_effect(plan, set(effect.store_names))
    active_store_name = None
    sell_threshold = None
    if rebalancing_effect is not None:
        active_store_name = rebalancing_effect.parameters.get("active_store_name")
        sell_threshold = rebalancing_effect.parameters.get("sell_threshold")

    return {
        "asset_class_store_name": asset_class_store_name,
        "positions": positions,
        "active_store_name": active_store_name,
        "sell_threshold": sell_threshold,
    }


def remove_position(plan: Plan, store_name: str) -> None:
    """Remove one position (store) from its asset class.

    Refuses to remove the last remaining position of an asset class - that
    would delete the whole asset class rather than one position; use
    core_remove_effect and manual cleanup for that instead. Also refuses to
    remove a position currently marked active for savings-rate priority (see
    `find_positions_rebalancing_effect`) - a new active position must be
    designated first rather than silently picking one or leaving the plan
    inconsistent.
    """
    effect = None
    for candidate in plan.effects:
        if isinstance(candidate, CorrelatedReturnEffect) and store_name in candidate.store_names:
            effect = candidate
            break
    if effect is None:
        msg = f"store {store_name!r} is not a tracked position in plan {plan.name!r}"
        raise ValueError(msg)

    if len(effect.store_names) == 1:
        msg = (
            f"{store_name!r} is the only position of its asset class; removing it "
            "would remove the whole asset class - use core_remove_effect and manual "
            "cleanup instead"
        )
        raise ValueError(msg)

    rebalancing_effect = find_positions_rebalancing_effect(plan, set(effect.store_names))
    if rebalancing_effect is not None:
        if rebalancing_effect.parameters.get("active_store_name") == store_name:
            msg = (
                f"{store_name!r} is the active position for its asset class; "
                "designate a new active position first"
            )
            raise ValueError(msg)
        rebalancing_store_names = rebalancing_effect.parameters.get("store_names", [])
        if store_name in rebalancing_store_names:
            rebalancing_store_names.remove(store_name)
            rebalancing_effect.parameters["store_names"] = rebalancing_store_names

    effect.store_names.remove(store_name)
    plan.stores = [store for store in plan.stores if store.name != store_name]
