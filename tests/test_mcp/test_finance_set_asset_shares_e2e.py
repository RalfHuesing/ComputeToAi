"""End-to-end tests for finance_set_asset_shares over a real MCP ClientSession.

Uses an in-memory client/server session (`mcp.shared.memory`) instead of the
real stdio subprocess used elsewhere in tests/test_mcp/, so the live-price
HTTP call can be mocked the same way tests/test_features/test_finance/
test_live_price.py mocks it - a subprocess would run in a separate process
where monkeypatching the parent process's modules has no effect.
"""

import json
import urllib.request
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import TextContent

from compute_to_ai.features.finance import live_price as live_price_module
from compute_to_ai.mcp.server import create_server
from compute_to_ai.mcp.settings import Settings

_FIXTURE_HTML = (
    Path(__file__).parent.parent
    / "test_features"
    / "test_finance"
    / "fixtures"
    / "ariva_instrument_page.html"
).read_text(encoding="utf-8")
_RESOLVED_URL = "https://www.ariva.de/etf/amundi-core-msci-world-swap-ucits-etf-dist"
_ISIN = "LU2572257124"


class _FakeResponse:
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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _mock_ariva(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        assert timeout > 0
        if "boerse_id" in request.full_url:
            return _FakeResponse(request.full_url, _FIXTURE_HTML.encode("utf-8"))
        return _FakeResponse(_RESOLVED_URL)

    monkeypatch.setattr(live_price_module.urllib.request, "urlopen", fake_urlopen)


async def _call_ok(session: ClientSession, tool_name: str, **arguments: object) -> str:
    result = await session.call_tool(tool_name, arguments)
    assert not result.isError, result.content
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


@pytest.mark.anyio
async def test_finance_set_asset_shares_sets_market_value_and_registry(tmp_path: Path) -> None:
    working_directory = tmp_path / "work"
    working_directory.mkdir()
    server = create_server(Settings(working_directory=working_directory))

    async with create_connected_server_and_client_session(server) as session:
        await _call_ok(session, "core_create_plan", plan_name="depot", step_count=10)
        await _call_ok(
            session,
            "finance_add_asset_class",
            plan_name="depot",
            store_name="equity",
            initial_balance=0.0,
            expected_return=0.07,
            volatility=0.15,
        )

        status = await _call_ok(
            session,
            "finance_set_asset_shares",
            plan_name="depot",
            store_name="equity",
            shares=10.0,
            isin_or_wkn=_ISIN,
        )
        assert "equity" in status

        stores_text = await _call_ok(session, "core_list_stores", plan_name="depot")
        stores = json.loads(stores_text)["stores"]
        equity = next(store for store in stores if store["name"] == "equity")
        assert equity["balance"] == pytest.approx(10.0 * 119.49)

    positions_file = working_directory / "depot" / "positions.json"
    positions = json.loads(positions_file.read_text(encoding="utf-8"))
    assert positions["positions"]["equity"]["isin_or_wkn"] == _ISIN
    assert positions["positions"]["equity"]["shares"] == pytest.approx(10.0)
    assert positions["positions"]["equity"]["exchange"] == "Xetra"


@pytest.mark.anyio
async def test_finance_set_asset_shares_requires_existing_store(tmp_path: Path) -> None:
    working_directory = tmp_path / "work"
    working_directory.mkdir()
    server = create_server(Settings(working_directory=working_directory))

    async with create_connected_server_and_client_session(server) as session:
        await _call_ok(session, "core_create_plan", plan_name="depot", step_count=10)

        result = await session.call_tool(
            "finance_set_asset_shares",
            {
                "plan_name": "depot",
                "store_name": "does-not-exist",
                "shares": 10.0,
                "isin_or_wkn": _ISIN,
            },
        )

    assert result.isError


@pytest.mark.anyio
async def test_finance_set_asset_shares_called_twice_fully_replaces_position(
    tmp_path: Path,
) -> None:
    working_directory = tmp_path / "work"
    working_directory.mkdir()
    server = create_server(Settings(working_directory=working_directory))

    async with create_connected_server_and_client_session(server) as session:
        await _call_ok(session, "core_create_plan", plan_name="depot", step_count=10)
        await _call_ok(
            session,
            "finance_add_asset_class",
            plan_name="depot",
            store_name="equity",
            initial_balance=0.0,
            expected_return=0.07,
            volatility=0.15,
        )

        await _call_ok(
            session,
            "finance_set_asset_shares",
            plan_name="depot",
            store_name="equity",
            shares=10.0,
            isin_or_wkn=_ISIN,
        )
        await _call_ok(
            session,
            "finance_set_asset_shares",
            plan_name="depot",
            store_name="equity",
            shares=3.0,
            isin_or_wkn=_ISIN,
        )

        stores_text = await _call_ok(session, "core_list_stores", plan_name="depot")
        stores = json.loads(stores_text)["stores"]
        equity = next(store for store in stores if store["name"] == "equity")
        assert equity["balance"] == pytest.approx(3.0 * 119.49)

    positions_file = working_directory / "depot" / "positions.json"
    positions = json.loads(positions_file.read_text(encoding="utf-8"))
    assert positions["positions"]["equity"]["shares"] == pytest.approx(3.0)
