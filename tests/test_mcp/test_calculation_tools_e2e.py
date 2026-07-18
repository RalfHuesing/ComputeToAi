"""End-to-end check that the calculation tools are wired into the real
stdio server under their calculations_ names. The formulas themselves are
covered by tests/test_features/test_calculations/; this only proves the
MCP registration works, not every formula again.
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


@pytest.mark.anyio
async def test_calculation_tools_are_registered_and_callable(
    server_params: StdioServerParameters,
) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        tools = await session.list_tools()
        tool_names = {tool.name for tool in tools.tools}
        assert "calculations_years_between" in tool_names
        assert "calculations_future_value_lump_sum" in tool_names
        assert "calculations_loan_monthly_payment" in tool_names

        result = await session.call_tool(
            "calculations_future_value_lump_sum",
            {"principal": 100.0, "annual_rate": 1.0, "years": 1},
        )

    assert not result.isError
    content = result.content[0]
    assert isinstance(content, TextContent)
    assert json.loads(content.text) == 200.0
