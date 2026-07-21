"""Live price query MCP tools."""

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from compute_to_ai.features.finance.live_price import LivePrice, get_live_price

logger = logging.getLogger(__name__)


def register_live_price_tools(mcp: FastMCP, _working_directory: Path) -> None:
    @mcp.tool()
    def finance_get_live_price(  # pyright: ignore[reportUnusedFunction]
        isin_or_wkn: str, exchange: str = "Xetra"
    ) -> LivePrice:
        """Look up an ETF's/fund's current price on Ariva.de by ISIN or WKN.

        Stateless, without needing a Plan - usable directly for any
        instrument, e.g. to check a price before deciding on a purchase.
        """
        result = get_live_price(isin_or_wkn, exchange)
        logger.info(
            "finance_get_live_price: isin_or_wkn=%r exchange=%r status=ok",
            isin_or_wkn,
            exchange,
        )
        logger.debug("finance_get_live_price result: %s", result.model_dump())
        return result
