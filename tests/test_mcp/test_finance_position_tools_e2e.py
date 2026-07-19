"""End-to-end tests for finance_add_position/finance_list_positions/
finance_remove_position/finance_set_position_from_transactions over the real
stdio transport - none of these tools need network mocking (unlike
finance_set_asset_shares/finance_update_plan_prices), so this uses the plain
stdio-subprocess pattern from test_finance_tools_e2e.py.
"""

import json
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

from compute_to_ai.mcp.settings import SETTINGS_PATH_ENV_VAR

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def server_params(tmp_path: Path) -> StdioServerParameters:
    working_directory = tmp_path / "work"
    working_directory.mkdir()
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text(
        f'working_directory = "{working_directory.as_posix()}"\n', encoding="utf-8"
    )
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "compute_to_ai.mcp.server"],
        cwd=str(REPO_ROOT),
        env={SETTINGS_PATH_ENV_VAR: str(settings_file)},
    )


async def _call_ok(session: ClientSession, tool_name: str, **arguments: object) -> str:
    result = await session.call_tool(tool_name, arguments)
    assert not result.isError, result.content
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


async def _setup_asset_class_plan(session: ClientSession, plan_name: str) -> None:
    await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=10)
    await _call_ok(
        session,
        "finance_add_asset_class",
        plan_name=plan_name,
        store_name="world_a",
        initial_balance=1000.0,
        expected_return=0.07,
        volatility=0.15,
    )


@pytest.mark.anyio
async def test_finance_add_position_and_list_positions(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "depot"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _setup_asset_class_plan(session, plan_name)

        status = await _call_ok(
            session,
            "finance_add_position",
            plan_name=plan_name,
            asset_class_store_name="world_a",
            store_name="world_b",
        )
        assert "world_b" in status

        list_text = await _call_ok(
            session, "finance_list_positions", plan_name=plan_name, asset_class_store_name="world_a"
        )
        result = json.loads(list_text)
        assert result["asset_class_store_name"] == "world_a"
        store_names = {position["store_name"] for position in result["positions"]}
        assert store_names == {"world_a", "world_b"}
        assert result["active_store_name"] is None
        assert result["sell_threshold"] is None

        world_b = next(p for p in result["positions"] if p["store_name"] == "world_b")
        assert world_b["balance"] == pytest.approx(0.0)

        effects_text = await _call_ok(session, "core_list_effects", plan_name=plan_name)
        effects = json.loads(effects_text)["effects"]
        return_effect = next(e for e in effects if e["type"] == "correlated_return")
        assert set(return_effect["store_names"]) == {"world_a", "world_b"}


@pytest.mark.anyio
async def test_finance_add_position_requires_existing_asset_class(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "depot"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=10)

        result = await session.call_tool(
            "finance_add_position",
            {
                "plan_name": plan_name,
                "asset_class_store_name": "does-not-exist",
                "store_name": "world_b",
            },
        )

    assert result.isError


@pytest.mark.anyio
async def test_finance_add_position_rejects_duplicate_store_name(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "depot"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _setup_asset_class_plan(session, plan_name)

        result = await session.call_tool(
            "finance_add_position",
            {
                "plan_name": plan_name,
                "asset_class_store_name": "world_a",
                "store_name": "world_a",
            },
        )

    assert result.isError


@pytest.mark.anyio
async def test_finance_remove_position_removes_from_effect_and_stores(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "depot"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _setup_asset_class_plan(session, plan_name)
        await _call_ok(
            session,
            "finance_add_position",
            plan_name=plan_name,
            asset_class_store_name="world_a",
            store_name="world_b",
        )

        status = await _call_ok(
            session, "finance_remove_position", plan_name=plan_name, store_name="world_b"
        )
        assert "world_b" in status

        stores_text = await _call_ok(session, "core_list_stores", plan_name=plan_name)
        store_names = {store["name"] for store in json.loads(stores_text)["stores"]}
        assert "world_b" not in store_names

        effects_text = await _call_ok(session, "core_list_effects", plan_name=plan_name)
        effects = json.loads(effects_text)["effects"]
        return_effect = next(e for e in effects if e["type"] == "correlated_return")
        assert "world_b" not in return_effect["store_names"]


@pytest.mark.anyio
async def test_finance_remove_position_rejects_removing_last_position(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "depot"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _setup_asset_class_plan(session, plan_name)

        result = await session.call_tool(
            "finance_remove_position", {"plan_name": plan_name, "store_name": "world_a"}
        )

    assert result.isError


@pytest.mark.anyio
async def test_finance_set_position_from_transactions_sets_cost_basis_and_registry(
    tmp_path: Path, server_params: StdioServerParameters
) -> None:
    plan_name = "depot"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _setup_asset_class_plan(session, plan_name)
        await _call_ok(
            session,
            "finance_add_position",
            plan_name=plan_name,
            asset_class_store_name="world_a",
            store_name="world_b",
        )

        transactions = [
            {"date": "2020-01-01", "shares": 10.0, "price": 100.0},
            {"date": "2021-01-01", "shares": -4.0, "price": 150.0},
        ]
        status = await _call_ok(
            session,
            "finance_set_position_from_transactions",
            plan_name=plan_name,
            store_name="world_b",
            transactions=transactions,
            isin_or_wkn="IE00BK1PV551",
        )
        assert "world_b" in status

        stores_text = await _call_ok(session, "core_list_stores", plan_name=plan_name)
        stores = json.loads(stores_text)["stores"]
        world_b = next(store for store in stores if store["name"] == "world_b")
        # A sell withdraws shares * price (money-denominated, matching how
        # Lots are recorded) from the currency lot balance: 4 * 150 = 600,
        # so the resulting cost-basis balance is 1000 - 600 (see
        # apply_transaction_history), not today's market value.
        assert world_b["balance"] == pytest.approx(1000.0 - 4.0 * 150.0)

    positions_file = tmp_path / "work" / plan_name / "positions.json"
    positions = json.loads(positions_file.read_text(encoding="utf-8"))
    world_b_meta = positions["positions"]["world_b"]
    assert world_b_meta["isin_or_wkn"] == "IE00BK1PV551"
    assert world_b_meta["shares"] == pytest.approx(6.0)
    assert world_b_meta["exchange"] == "Xetra"
