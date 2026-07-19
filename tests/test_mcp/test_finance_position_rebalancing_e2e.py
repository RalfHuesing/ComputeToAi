"""End-to-end test for finance_add_position_rebalancing over the real stdio
transport - drives a full multi-step simulation through core_run_simulation,
not just the pure function in isolation (see test_positions_rebalancing.py
for that), to confirm the shortfall-cover job actually happens through a
real Plan/tool-call path.
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


@pytest.mark.anyio
async def test_position_rebalancing_covers_shortfall_from_sibling_e2e(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "depot"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=2)

        # Active position "world_a" starts at 1000, zero return so the
        # numbers stay exact.
        await _call_ok(
            session,
            "finance_add_asset_class",
            plan_name=plan_name,
            store_name="world_a",
            initial_balance=1000.0,
            expected_return=0.0,
            volatility=0.0,
        )
        await _call_ok(
            session,
            "finance_add_position",
            plan_name=plan_name,
            asset_class_store_name="world_a",
            store_name="world_b",
        )
        # Value the sibling "world_b" offline via a priced transaction
        # (no network lookup needed) at 10 shares * 50 = 500.
        await _call_ok(
            session,
            "finance_set_position_from_transactions",
            plan_name=plan_name,
            store_name="world_b",
            transactions=[{"date": "2020-01-01", "shares": 10.0, "price": 50.0}],
            isin_or_wkn="IE00BK1PV551",
        )

        await _call_ok(
            session,
            "finance_add_position_rebalancing",
            plan_name=plan_name,
            store_names=["world_a", "world_b"],
            active_store_name="world_a",
        )

        # Step 0: savings flow entirely into the active position (world_a):
        # 1000 + 200 = 1200. world_b stays at 500 (no growth configured).
        await _call_ok(
            session,
            "finance_add_income_stream",
            plan_name=plan_name,
            name="Sparrate",
            store_name="world_a",
            amount=200.0,
            start_step=0,
            end_step=0,
        )
        # Step 1: a retirement-gap-style withdrawal of 1500 exceeds
        # world_a's 1200 alone, forcing job (a) to draw the 300 shortfall
        # from world_b.
        await _call_ok(
            session,
            "finance_add_expense",
            plan_name=plan_name,
            name="Entnahme",
            store_name="world_a",
            amount=1500.0,
            start_step=1,
            end_step=1,
        )

        await _call_ok(session, "core_run_simulation", plan_name=plan_name)
        result_text = await _call_ok(
            session, "core_get_result", plan_name=plan_name, include_time_series=True
        )
        result = json.loads(result_text)

    # world_a: 1000 + 200 - 1500 = -300, fully covered by world_b -> 0.
    # world_b: 500 - 300 = 200, the sibling's balance actually decreased.
    assert result["final_balances"]["world_a"] == pytest.approx(0.0)
    assert result["final_balances"]["world_b"] == pytest.approx(200.0)
    assert result["time_series"][0]["world_a"] == pytest.approx(1200.0)
    assert result["time_series"][0]["world_b"] == pytest.approx(500.0)
