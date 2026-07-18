"""End-to-end test over the real stdio transport: spawns the server as a
subprocess, exactly how an agent would, and drives the golden path purely
through MCP tool calls (not the engine's Python API).
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


async def _call_ok(session: ClientSession, name: str, **arguments: object) -> str:
    result = await session.call_tool(name, arguments)
    assert not result.isError, result.content
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


@pytest.mark.anyio
async def test_golden_path_100_euro_per_month_zero_return_40_years(
    server_params: StdioServerParameters,
) -> None:
    """100 €/month, 0 % return, 40 years (480 months) -> 48,000 €, driven
    entirely through MCP tool calls over stdio."""
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="retirement-baseline", step_count=480)
        await _call_ok(
            session, "core_add_store", plan_name="retirement-baseline", store_name="portfolio"
        )
        await _call_ok(
            session,
            "core_add_effect",
            plan_name="retirement-baseline",
            store_name="portfolio",
            amount_per_step=100.0,
        )
        await _call_ok(session, "core_run_simulation", plan_name="retirement-baseline")
        result_text = await _call_ok(session, "core_get_result", plan_name="retirement-baseline")

    payload = json.loads(result_text)
    assert payload["final_balances"]["portfolio"] == 48_000.0


@pytest.mark.anyio
async def test_add_store_on_unknown_plan_is_a_tool_error(
    server_params: StdioServerParameters,
) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool(
            "core_add_store", {"plan_name": "does-not-exist", "store_name": "x"}
        )

    assert result.isError


@pytest.mark.anyio
async def test_docs_are_exposed_as_resources(server_params: StdioServerParameters) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        resources = await session.list_resources()

    uris = {str(resource.uri) for resource in resources.resources}
    assert "docs://00-Vision.md" in uris
    assert "docs://prompts/finance_de/finanzberater.md" in uris
