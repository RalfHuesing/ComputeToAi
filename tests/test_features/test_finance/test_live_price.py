"""Tests for live_price.py - see Docs/10-Roadmap.md, Meilenstein 4, Epic 4.1."""

import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path

import pytest

from compute_to_ai.features.finance import live_price as live_price_module
from compute_to_ai.features.finance.live_price import get_live_price

_FIXTURE_HTML = (
    Path(__file__).parent / "fixtures" / "ariva_instrument_page.html"
).read_text(encoding="utf-8")
_RESOLVED_URL = "https://www.ariva.de/etf/amundi-core-msci-world-swap-ucits-etf-dist"


class _FakeResponse:
    """Minimal stand-in for the context-manager `http.client.HTTPResponse`."""

    def __init__(self, url: str, body: bytes = b"") -> None:
        self._url = url
        self._body = body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def geturl(self) -> str:
        return self._url

    def read(self) -> bytes:
        return self._body


def test_get_live_price_parses_real_markup(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        assert timeout > 0
        calls.append(request.full_url)
        if "boerse_id" in request.full_url:
            return _FakeResponse(request.full_url, _FIXTURE_HTML.encode("utf-8"))
        return _FakeResponse(_RESOLVED_URL)

    monkeypatch.setattr(live_price_module.urllib.request, "urlopen", fake_urlopen)

    result = get_live_price("LU2572257124", "Xetra")

    assert result.name == "Amundi Core MSCI World Swap UCITS ETF Dist"
    assert result.isin == "LU2572257124"
    assert result.wkn == "ETF018"
    assert result.price == pytest.approx(119.49)
    assert result.currency == "EUR"
    assert result.exchange == "Xetra"
    assert result.as_of == "17.07.26"
    assert calls == [
        "https://www.ariva.de/LU2572257124",
        f"{_RESOLVED_URL}?boerse_id=45",
    ]


def test_get_live_price_rejects_unknown_exchange() -> None:
    with pytest.raises(ValueError, match="unknown exchange"):
        get_live_price("LU2572257124", "NYSE")


def test_get_live_price_raises_for_unknown_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        assert timeout > 0
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", Message(), None)

    monkeypatch.setattr(live_price_module.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="no instrument found"):
        get_live_price("XX0000000000")


def test_get_live_price_raises_when_markup_changed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        assert timeout > 0
        if "boerse_id" in request.full_url:
            return _FakeResponse(request.full_url, b"<html>no price here</html>")
        return _FakeResponse(_RESOLVED_URL)

    monkeypatch.setattr(live_price_module.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="could not parse"):
        get_live_price("LU2572257124")


def test_get_live_price_online_smoke() -> None:
    """Hits the real Ariva.de endpoint to catch markup drift early; skipped
    without network access rather than failing the whole suite."""
    try:
        result = get_live_price("LU2572257124", "Xetra")
    except (urllib.error.URLError, TimeoutError) as error:
        pytest.skip(f"no network access: {error}")

    assert result.isin == "LU2572257124"
    assert result.wkn == "ETF018"
    assert result.price > 0
    assert result.currency == "EUR"
