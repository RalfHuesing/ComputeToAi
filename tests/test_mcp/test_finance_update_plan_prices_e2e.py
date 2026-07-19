"""End-to-end tests for finance_update_plan_prices over a real MCP ClientSession.

Uses an in-memory client/server session (`mcp.shared.memory`), same rationale
as test_finance_set_asset_shares_e2e.py: the live-price HTTP call needs to be
mocked, which a real stdio subprocess would not allow from the parent
process's monkeypatch.
"""

import json
import urllib.error
import urllib.request
from email.message import Message
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
_EQUITY_ISIN = "LU2572257124"
_BOND_ISIN = "XX0000000000"


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


async def _call_ok(session: ClientSession, tool_name: str, **arguments: object) -> str:
    result = await session.call_tool(tool_name, arguments)
    assert not result.isError, result.content
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


@pytest.mark.anyio
async def test_finance_update_plan_prices_skips_failing_position_but_updates_others(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two registered positions, one whose ISIN starts resolving to a 404
    only once the plan is already set up (simulating an instrument that
    becomes unreachable later) - the other must still be refreshed."""
    bond_should_fail = {"value": False}

    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        assert timeout > 0
        full_url = request.full_url
        if "boerse_id" in full_url:
            return _FakeResponse(full_url, _FIXTURE_HTML.encode("utf-8"))
        if _BOND_ISIN in full_url and bond_should_fail["value"]:
            raise urllib.error.HTTPError(full_url, 404, "Not Found", Message(), None)
        return _FakeResponse(_RESOLVED_URL)

    monkeypatch.setattr(live_price_module.urllib.request, "urlopen", fake_urlopen)

    working_directory = tmp_path / "work"
    working_directory.mkdir()
    server = create_server(Settings(working_directory=working_directory))
    plan_name = "depot"

    async with create_connected_server_and_client_session(server) as session:
        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=10)
        await _call_ok(
            session,
            "finance_add_asset_class",
            plan_name=plan_name,
            store_name="equity",
            initial_balance=0.0,
            expected_return=0.07,
            volatility=0.15,
        )
        await _call_ok(
            session,
            "finance_add_asset_class",
            plan_name=plan_name,
            store_name="bond",
            initial_balance=0.0,
            expected_return=0.03,
            volatility=0.05,
        )

        await _call_ok(
            session,
            "finance_set_asset_shares",
            plan_name=plan_name,
            store_name="equity",
            shares=10.0,
            isin_or_wkn=_EQUITY_ISIN,
        )
        await _call_ok(
            session,
            "finance_set_asset_shares",
            plan_name=plan_name,
            store_name="bond",
            shares=5.0,
            isin_or_wkn=_BOND_ISIN,
        )

        bond_should_fail["value"] = True

        result_text = await _call_ok(
            session, "finance_update_plan_prices", plan_name=plan_name
        )

    payload = json.loads(result_text)
    assert [update["store_name"] for update in payload["updated"]] == ["equity"]
    assert "bond" in payload["skipped"]
    assert "no instrument found" in payload["skipped"]["bond"]


@pytest.mark.anyio
async def test_finance_update_plan_prices_skips_position_whose_store_was_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        assert timeout > 0
        if "boerse_id" in request.full_url:
            return _FakeResponse(request.full_url, _FIXTURE_HTML.encode("utf-8"))
        return _FakeResponse(_RESOLVED_URL)

    monkeypatch.setattr(live_price_module.urllib.request, "urlopen", fake_urlopen)

    working_directory = tmp_path / "work"
    working_directory.mkdir()
    server = create_server(Settings(working_directory=working_directory))
    plan_name = "depot"

    async with create_connected_server_and_client_session(server) as session:
        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=10)
        await _call_ok(
            session,
            "finance_add_asset_class",
            plan_name=plan_name,
            store_name="equity",
            initial_balance=0.0,
            expected_return=0.07,
            volatility=0.15,
        )
        await _call_ok(
            session,
            "finance_set_asset_shares",
            plan_name=plan_name,
            store_name="equity",
            shares=10.0,
            isin_or_wkn=_EQUITY_ISIN,
        )

        # Remove the effect referencing the store, then rewrite the plan
        # file with the store itself dropped, simulating a store that
        # disappeared out from under a still-registered position.
        plan_file = working_directory / plan_name / "plan.json"
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        plan_data["stores"] = [s for s in plan_data["stores"] if s["name"] != "equity"]
        plan_data["effects"] = [
            e for e in plan_data["effects"] if e.get("store_name") != "equity"
        ]
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")

        result_text = await _call_ok(
            session, "finance_update_plan_prices", plan_name=plan_name
        )

    payload = json.loads(result_text)
    assert payload["updated"] == []
    assert payload["skipped"]["equity"] == "store no longer exists in plan"
