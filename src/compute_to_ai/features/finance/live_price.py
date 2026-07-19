"""Live price lookup for ETFs/funds by ISIN or WKN via Ariva.de.

See Docs/10-Roadmap.md, Meilenstein 4, Epic 4.1.
"""

import re
import urllib.error
import urllib.request
from datetime import UTC, datetime

from pydantic import BaseModel

_USER_AGENT = "Mozilla/5.0 (compatible; ComputeToAi/1.0)"
_TIMEOUT_SECONDS = 10

# Exchange -> Ariva `boerse_id` query parameter, see Docs/10-Roadmap.md.
_EXCHANGE_IDS: dict[str, int] = {
    "Xetra": 45,
    "Tradegate": 131,
    "L&S": 16,
    "Gettex": 207,
}

_NAME_PATTERN = re.compile(r'data-cy="instrument-name"[^>]*>\s*([^<]+?)\s*</h1>')
_WKN_PATTERN = re.compile(r'id="WKN-copy"[\s\S]*?class="value">([^<]+)<')
_ISIN_PATTERN = re.compile(r'id="ISIN-copy"[\s\S]*?class="value">([^<]+)<')
_PRICE_PATTERN = re.compile(r'class="instrument-header-quote">\s*([\d.,]+)\s*&nbsp;&(\w+);')
_TIME_PATTERN = re.compile(r'class="instrument-header-last-time">\s*<span>([^<]+)</span>')

_CURRENCY_ENTITIES = {"euro": "EUR"}


class LivePrice(BaseModel):
    """Result of a single live price lookup on one exchange."""

    name: str
    isin: str
    wkn: str
    price: float
    currency: str
    exchange: str
    as_of: str
    queried_at: str


def get_live_price(isin_or_wkn: str, exchange: str = "Xetra") -> LivePrice:
    """Fetch the current price of an ETF/fund from Ariva.de by ISIN or WKN.

    Two-stage lookup: Ariva redirects a bare ISIN/WKN to the instrument's
    page, which by itself defaults to an unpredictable exchange - the
    resolved URL is re-requested with the exchange's `boerse_id` appended to
    pin down the actual quote source.
    """
    if exchange not in _EXCHANGE_IDS:
        msg = f"unknown exchange {exchange!r}, must be one of {sorted(_EXCHANGE_IDS)}"
        raise ValueError(msg)

    resolved_url = _resolve_instrument_url(isin_or_wkn)
    html = _fetch(f"{resolved_url}?boerse_id={_EXCHANGE_IDS[exchange]}")

    name_match = _NAME_PATTERN.search(html)
    wkn_match = _WKN_PATTERN.search(html)
    isin_match = _ISIN_PATTERN.search(html)
    price_match = _PRICE_PATTERN.search(html)
    time_match = _TIME_PATTERN.search(html)
    if not (name_match and wkn_match and isin_match and price_match and time_match):
        msg = f"could not parse Ariva.de price page for {isin_or_wkn!r} - markup may have changed"
        raise ValueError(msg)

    price = float(price_match.group(1).replace(".", "").replace(",", "."))
    currency = _CURRENCY_ENTITIES.get(price_match.group(2), price_match.group(2).upper())

    return LivePrice(
        name=name_match.group(1),
        isin=isin_match.group(1),
        wkn=wkn_match.group(1),
        price=price,
        currency=currency,
        exchange=exchange,
        as_of=time_match.group(1),
        queried_at=datetime.now(UTC).isoformat(),
    )


def _resolve_instrument_url(isin_or_wkn: str) -> str:
    """Follow Ariva's redirect from a bare ISIN/WKN to its instrument page."""
    request = urllib.request.Request(
        f"https://www.ariva.de/{isin_or_wkn}", headers={"User-Agent": _USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return response.geturl()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            msg = f"no instrument found for {isin_or_wkn!r} on Ariva.de"
            raise ValueError(msg) from error
        raise


def _fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8")
