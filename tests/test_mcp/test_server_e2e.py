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


async def _call_ok(session: ClientSession, tool_name: str, **arguments: object) -> str:
    result = await session.call_tool(tool_name, arguments)
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
            name="Contribution",
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


@pytest.mark.anyio
async def test_duplicate_rename_and_delete_plan(server_params: StdioServerParameters) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="original", step_count=10)
        await _call_ok(session, "core_add_store", plan_name="original", store_name="cash")
        await _call_ok(
            session,
            "core_add_effect",
            plan_name="original",
            store_name="cash",
            name="Contribution",
            amount_per_step=10.0,
        )

        # Duplicate carries the configuration over, independently of the original.
        await _call_ok(
            session, "core_duplicate_plan", plan_name="original", new_plan_name="variant"
        )
        stores_text = await _call_ok(session, "core_list_stores", plan_name="variant")
        assert json.loads(stores_text)["stores"][0]["name"] == "cash"

        # Duplicating onto an existing name is rejected.
        dup_conflict = await session.call_tool(
            "core_duplicate_plan", {"plan_name": "original", "new_plan_name": "variant"}
        )
        assert dup_conflict.isError

        # Rename moves the plan; the old name is gone, the new one works.
        await _call_ok(session, "core_rename_plan", plan_name="variant", new_plan_name="renamed")
        renamed_missing = await session.call_tool("core_list_stores", {"plan_name": "variant"})
        assert renamed_missing.isError
        stores_text = await _call_ok(session, "core_list_stores", plan_name="renamed")
        assert json.loads(stores_text)["stores"][0]["name"] == "cash"

        # Delete removes the plan entirely.
        await _call_ok(session, "core_delete_plan", plan_name="renamed")
        deleted_missing = await session.call_tool("core_list_stores", {"plan_name": "renamed"})
        assert deleted_missing.isError

        # The original plan was never touched by any of the above.
        original_stores = await _call_ok(session, "core_list_stores", plan_name="original")
        assert json.loads(original_stores)["stores"][0]["name"] == "cash"


@pytest.mark.anyio
async def test_list_and_remove_effect(server_params: StdioServerParameters) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="effects-test", step_count=5)
        await _call_ok(session, "core_add_store", plan_name="effects-test", store_name="cash")
        await _call_ok(
            session,
            "finance_add_income_stream",
            plan_name="effects-test",
            name="Gehalt",
            store_name="cash",
            amount=1000.0,
        )

        effects_text = await _call_ok(session, "core_list_effects", plan_name="effects-test")
        effect_names = {effect["name"] for effect in json.loads(effects_text)["effects"]}
        assert effect_names == {"Gehalt"}

        # Removing an unknown name fails clearly.
        unknown = await session.call_tool(
            "core_remove_effect", {"plan_name": "effects-test", "effect_name": "does-not-exist"}
        )
        assert unknown.isError

        await _call_ok(
            session, "core_remove_effect", plan_name="effects-test", effect_name="Gehalt"
        )
        effects_text = await _call_ok(session, "core_list_effects", plan_name="effects-test")
        assert json.loads(effects_text)["effects"] == []


@pytest.mark.anyio
async def test_remove_effect_is_rejected_when_name_is_ambiguous(
    server_params: StdioServerParameters,
) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="ambiguous-test", step_count=5)
        await _call_ok(session, "core_add_store", plan_name="ambiguous-test", store_name="cash")
        for _ in range(2):
            await _call_ok(
                session,
                "finance_add_income_stream",
                plan_name="ambiguous-test",
                name="Gehalt",
                store_name="cash",
                amount=1000.0,
            )

        result = await session.call_tool(
            "core_remove_effect", {"plan_name": "ambiguous-test", "effect_name": "Gehalt"}
        )
        assert result.isError

        # Neither effect was removed by the failed, ambiguous attempt.
        effects_text = await _call_ok(session, "core_list_effects", plan_name="ambiguous-test")
        assert len(json.loads(effects_text)["effects"]) == 2


@pytest.mark.anyio
async def test_core_add_transfer_moves_a_fixed_amount_split_by_weight(
    server_params: StdioServerParameters,
) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="transfer-test", step_count=1)
        await _call_ok(
            session,
            "core_add_store",
            plan_name="transfer-test",
            store_name="cash",
            initial_balance=1000.0,
        )
        await _call_ok(session, "core_add_store", plan_name="transfer-test", store_name="etf_a")
        await _call_ok(session, "core_add_store", plan_name="transfer-test", store_name="etf_b")

        await _call_ok(
            session,
            "core_add_transfer",
            plan_name="transfer-test",
            from_store_name="cash",
            to_store_weights={"etf_a": 0.6, "etf_b": 0.4},
            amount=100.0,
        )
        await _call_ok(session, "core_run_simulation", plan_name="transfer-test")
        result_text = await _call_ok(session, "core_get_result", plan_name="transfer-test")

    payload = json.loads(result_text)
    assert payload["final_balances"]["cash"] == 900.0
    assert payload["final_balances"]["etf_a"] == 60.0
    assert payload["final_balances"]["etf_b"] == 40.0


@pytest.mark.anyio
async def test_core_add_transfer_rejects_unknown_store(
    server_params: StdioServerParameters,
) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(
            session, "core_create_plan", plan_name="transfer-unknown-store", step_count=1
        )
        await _call_ok(
            session, "core_add_store", plan_name="transfer-unknown-store", store_name="cash"
        )

        result = await session.call_tool(
            "core_add_transfer",
            {
                "plan_name": "transfer-unknown-store",
                "from_store_name": "cash",
                "to_store_weights": {"does-not-exist": 1.0},
                "amount": 100.0,
            },
        )

    assert result.isError


@pytest.mark.anyio
async def test_core_add_transfer_rejects_weights_not_summing_to_one(
    server_params: StdioServerParameters,
) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="transfer-bad-weights", step_count=1)
        await _call_ok(
            session, "core_add_store", plan_name="transfer-bad-weights", store_name="cash"
        )
        await _call_ok(
            session, "core_add_store", plan_name="transfer-bad-weights", store_name="etf"
        )

        result = await session.call_tool(
            "core_add_transfer",
            {
                "plan_name": "transfer-bad-weights",
                "from_store_name": "cash",
                "to_store_weights": {"etf": 0.5},
                "amount": 100.0,
            },
        )

    assert result.isError


@pytest.mark.anyio
async def test_core_list_phases(server_params: StdioServerParameters) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(
            session,
            "core_create_plan",
            plan_name="phases-list-test",
            step_count=100,
            steps_per_year=1,
        )

        # Initially empty
        phases_text = await _call_ok(session, "core_list_phases", plan_name="phases-list-test")
        payload = json.loads(phases_text)
        assert payload["phases"] == []

        # Add phases
        await _call_ok(
            session,
            "finance_set_life_phases",
            plan_name="phases-list-test",
            current_age=30,
            employment_end_age=60,
            statutory_pension_start_age=67,
            life_expectancy_age=90,
        )

        phases_text = await _call_ok(session, "core_list_phases", plan_name="phases-list-test")
        payload = json.loads(phases_text)
        phases = payload["phases"]

        assert len(phases) == 3
        # Employment, Early retirement gap, Pension
        assert phases[0]["name"] == "Erwerbsphase"
        assert phases[0]["start_step"] == 0
        assert phases[0]["end_step"] == 30
        assert phases[0]["description"] is None

        assert phases[1]["name"] == "Frühruhestandslücke"
        assert phases[1]["start_step"] == 30
        assert phases[1]["end_step"] == 37

        assert phases[2]["name"] == "Rentenphase"
        assert phases[2]["start_step"] == 37
        assert phases[2]["end_step"] == 60
