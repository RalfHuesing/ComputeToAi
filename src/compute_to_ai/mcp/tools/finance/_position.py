"""Position management MCP tools."""

import logging
import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.calculations.holdings import ShareTransaction, shares_from_transactions
from compute_to_ai.features.finance.live_price import get_live_price
from compute_to_ai.features.finance.position import (
    PositionMetadata,
    PositionPriceUpdate,
    PositionTransaction,
    PriceUpdateResult,
    add_position,
    apply_price_update,
    apply_transaction_history,
    list_positions,
    remove_position,
    set_position_balance,
)
from compute_to_ai.mcp.tools.plan_storage import load_plan, save_plan
from compute_to_ai.mcp.tools.position_storage import load_position_registry, save_position_registry

logger = logging.getLogger(__name__)


def register_position_tools(mcp: FastMCP, working_directory: Path) -> None:
    @mcp.tool()
    def finance_set_asset_shares(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        store_name: str,
        shares: float,
        isin_or_wkn: str,
        exchange: str = "Xetra",
    ) -> str:
        """Initialize/replace a position's balance from a live-quoted share count."""
        plan = load_plan(working_directory, plan_name)
        if store_name not in {store.name for store in plan.stores}:
            msg = (
                f"no store named {store_name!r} in plan {plan_name!r}; "
                "add it first with finance_add_asset_class"
            )
            raise ValueError(msg)

        price_info = get_live_price(isin_or_wkn, exchange)
        set_position_balance(plan.store(store_name), shares, price_info.price)
        save_plan(working_directory, plan)

        registry = load_position_registry(working_directory, plan_name)
        registry.positions[store_name] = PositionMetadata(
            isin_or_wkn=isin_or_wkn,
            shares=shares,
            exchange=exchange,
            last_updated=price_info.queried_at,
        )
        save_position_registry(working_directory, plan_name, registry)

        logger.info("finance_set_asset_shares: plan=%r store=%r status=ok", plan_name, store_name)
        logger.debug(
            "finance_set_asset_shares: shares=%s price=%s market_value=%s",
            shares,
            price_info.price,
            shares * price_info.price,
        )
        return (
            f"set {store_name!r} in plan {plan_name!r} to {shares} shares of {isin_or_wkn!r} "
            f"at {price_info.price} {price_info.currency} "
            f"(market value {shares * price_info.price:.2f} {price_info.currency})"
        )

    @mcp.tool()
    def finance_update_plan_prices(plan_name: str) -> PriceUpdateResult:  # pyright: ignore[reportUnusedFunction]
        """Refresh every registered position's balance from its current live price."""
        plan = load_plan(working_directory, plan_name)
        registry = load_position_registry(working_directory, plan_name)
        result = PriceUpdateResult()

        for store_name, meta in registry.positions.items():
            if store_name not in {store.name for store in plan.stores}:
                result.skipped[store_name] = "store no longer exists in plan"
                continue

            try:
                price_info = get_live_price(meta.isin_or_wkn, meta.exchange)
            except (ValueError, urllib.error.URLError, TimeoutError) as error:
                result.skipped[store_name] = str(error)
                continue

            store = plan.store(store_name)
            old_balance = store.balance
            apply_price_update(store, meta.shares, price_info.price)
            meta.last_updated = price_info.queried_at
            result.updated.append(
                PositionPriceUpdate(
                    store_name=store_name,
                    old_balance=old_balance,
                    new_balance=store.balance,
                    price=price_info.price,
                    currency=price_info.currency,
                )
            )

        save_plan(working_directory, plan)
        save_position_registry(working_directory, plan_name, registry)

        logger.info(
            "finance_update_plan_prices: plan=%r updated=%d skipped=%d status=ok",
            plan_name,
            len(result.updated),
            len(result.skipped),
        )
        logger.debug("finance_update_plan_prices result: %s", result.model_dump())
        return result

    @mcp.tool()
    def finance_add_position(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        asset_class_store_name: str,
        store_name: str,
        description: str | None = None,
    ) -> str:
        """Add a new, still-unvalued position (store) to an existing asset class."""
        plan = load_plan(working_directory, plan_name)
        add_position(plan, asset_class_store_name, store_name, description)
        save_plan(working_directory, plan)

        logger.info(
            "finance_add_position: plan=%r asset_class=%r store=%r status=ok",
            plan_name,
            asset_class_store_name,
            store_name,
        )
        return (
            f"added position {store_name!r} to asset class {asset_class_store_name!r} "
            f"in plan {plan_name!r}"
        )

    @mcp.tool()
    def finance_list_positions(  # pyright: ignore[reportUnusedFunction]
        plan_name: str, asset_class_store_name: str
    ) -> dict[str, Any]:
        """List every position (store) of one asset class with its current balance."""
        plan = load_plan(working_directory, plan_name)
        result = list_positions(plan, asset_class_store_name)

        logger.info(
            "finance_list_positions: plan=%r asset_class=%r positions=%d status=ok",
            plan_name,
            asset_class_store_name,
            len(result["positions"]),
        )
        return result

    @mcp.tool()
    def finance_remove_position(plan_name: str, store_name: str) -> str:  # pyright: ignore[reportUnusedFunction]
        """Remove one position (store) from its asset class."""
        plan = load_plan(working_directory, plan_name)
        remove_position(plan, store_name)
        save_plan(working_directory, plan)

        registry = load_position_registry(working_directory, plan_name)
        if store_name in registry.positions:
            del registry.positions[store_name]
            save_position_registry(working_directory, plan_name, registry)

        logger.info("finance_remove_position: plan=%r store=%r status=ok", plan_name, store_name)
        return f"removed position {store_name!r} from plan {plan_name!r}"

    @mcp.tool()
    def finance_set_position_from_transactions(  # pyright: ignore[reportUnusedFunction]
        plan_name: str,
        store_name: str,
        transactions: list[PositionTransaction],
        isin_or_wkn: str,
        exchange: str = "Xetra",
    ) -> str:
        """Rebuild a position's lots from a priced buy/sell transaction history."""
        plan = load_plan(working_directory, plan_name)
        if store_name not in {store.name for store in plan.stores}:
            msg = (
                f"no store named {store_name!r} in plan {plan_name!r}; "
                "add it first with finance_add_position"
            )
            raise ValueError(msg)

        apply_transaction_history(plan.store(store_name), transactions)
        total_shares = shares_from_transactions(
            [ShareTransaction(date=t.date, shares=t.shares) for t in transactions]
        )
        save_plan(working_directory, plan)

        registry = load_position_registry(working_directory, plan_name)
        registry.positions[store_name] = PositionMetadata(
            isin_or_wkn=isin_or_wkn,
            shares=total_shares,
            exchange=exchange,
            last_updated=datetime.now(UTC).isoformat(),
        )
        save_position_registry(working_directory, plan_name, registry)

        logger.info(
            "finance_set_position_from_transactions: plan=%r store=%r status=ok",
            plan_name,
            store_name,
        )
        logger.debug(
            "finance_set_position_from_transactions: total_shares=%s cost_basis_balance=%s",
            total_shares,
            plan.store(store_name).balance,
        )
        return (
            f"rebuilt position {store_name!r} in plan {plan_name!r} from "
            f"{len(transactions)} transactions ({total_shares} shares at cost basis); "
            "a price refresh via finance_update_plan_prices is still needed"
        )
