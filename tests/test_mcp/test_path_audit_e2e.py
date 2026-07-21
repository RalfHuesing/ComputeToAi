"""End-to-end test over the real stdio transport for the path-audit tools
(core_run_path_audit, finance_get_path_category_series,
finance_get_path_event_log) - the "Explainable AI" plausibility-check
building blocks (see Docs/04-Feature-Finanzen-Methodik.md, "Pfad-Audit und
Plausibilitätsprüfung"). Builds a small plan purely through MCP tool calls
(not the engine's Python API), matching the pattern in
tests/test_mcp/test_finance_tools_e2e.py.
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
async def test_path_audit_end_to_end(server_params: StdioServerParameters) -> None:
    plan_name = "path-audit-e2e"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(
            session, "core_create_plan", plan_name=plan_name, step_count=10, steps_per_year=1
        )
        await _call_ok(
            session, "core_add_store", plan_name=plan_name, store_name="cash", initial_balance=0.0
        )

        await _call_ok(
            session,
            "finance_set_life_phases",
            plan_name=plan_name,
            current_age=60,
            employment_end_age=63,
            statutory_pension_start_age=67,
            life_expectancy_age=70,
        )
        await _call_ok(
            session,
            "finance_add_income_stream",
            plan_name=plan_name,
            name="Gehalt",
            store_name="cash",
            amount=30000.0,
            active_phases=["Erwerbsphase"],
            frequency="yearly",
        )
        await _call_ok(
            session,
            "finance_add_expense",
            plan_name=plan_name,
            name="Lebenshaltung",
            store_name="cash",
            amount=18000.0,
            frequency="yearly",
        )
        await _call_ok(
            session,
            "finance_add_liability",
            plan_name=plan_name,
            name="Kredit",
            liability_store_name="kredit",
            cash_store_name="cash",
            principal=10000.0,
            interest_rate=0.03,
            payment=2000.0,
        )
        await _call_ok(
            session,
            "finance_add_asset_class",
            plan_name=plan_name,
            store_name="equity",
            initial_balance=1000.0,
            expected_return=0.05,
            volatility=0.10,
        )
        await _call_ok(
            session,
            "finance_set_target_condition",
            plan_name=plan_name,
            ruin_stores=["cash", "equity"],
        )

        await _call_ok(session, "core_run_path_audit", plan_name=plan_name, num_runs=30, seed=11)

        category_text = await _call_ok(
            session, "finance_get_path_category_series", plan_name=plan_name, path="deterministic"
        )
        event_log_text = await _call_ok(
            session, "finance_get_path_event_log", plan_name=plan_name, path="deterministic"
        )
        p50_category_text = await _call_ok(
            session,
            "finance_get_path_category_series",
            plan_name=plan_name,
            path="p50",
            granularity="monthly_average",
        )
        audit_text = await _call_ok(
            session, "finance_audit_plan", plan_name=plan_name, path="deterministic"
        )

    category_payload = json.loads(category_text)
    steps = category_payload["steps"]
    assert len(steps) == 10
    assert {"income", "expenses", "taxes", "returns", "reallocations", "balances"} <= set(steps[0])
    # Lebenshaltung (18,000) + Kredit Rate (2,000) - a liability's own
    # interest/principal bookkeeping must not double-count as a further
    # expense on top of the "Rate" payment already deducted from cash.
    assert steps[0]["expenses"] == pytest.approx(20000.0)

    event_payload = json.loads(event_log_text)
    event_types = {event["event_type"] for event in event_payload["events"]}
    assert "phase_transition" in event_types
    assert "liability_paid_off" in event_types

    p50_payload = json.loads(p50_category_text)
    assert len(p50_payload["steps"]) == 10

    audit_payload = json.loads(audit_text)
    # The liability is fully amortized within the 10-step timeline (see the
    # liability_paid_off event asserted above), so no unpaid-liability
    # finding should fire for it.
    assert not any("kredit" in finding["message"] for finding in audit_payload["findings"])


@pytest.mark.anyio
async def test_core_get_path_step_ledger_and_computed_states(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "path-audit-drilldown"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=6)
        await _call_ok(
            session,
            "core_add_store",
            plan_name=plan_name,
            store_name="risky",
            initial_balance=2000.0,
        )
        await _call_ok(
            session, "core_add_store", plan_name=plan_name, store_name="safe", initial_balance=0.0
        )
        await _call_ok(
            session,
            "finance_add_flexible_acquisition",
            plan_name=plan_name,
            name="Urlaub",
            amount=1000.0,
            target_step=5,
            tolerance_steps=1,
            risky_store_name="risky",
            safe_store_name="safe",
            glidepath_start_step=0,
        )

        await _call_ok(session, "core_run_path_audit", plan_name=plan_name, num_runs=5, seed=1)

        # Trigger fires at step 4 (see Docs/04, "Trigger-Logik", and
        # tests/test_features/test_finance/test_path_audit.py).
        ledger_text = await _call_ok(
            session,
            "core_get_path_step_ledger",
            plan_name=plan_name,
            path="deterministic",
            step=4,
        )
        states_text = await _call_ok(
            session, "core_get_path_computed_states", plan_name=plan_name, path="deterministic"
        )

    ledger_payload = json.loads(ledger_text)
    entries = ledger_payload["entries"]
    assert entries
    assert all(entry["step"] == 4 for entry in entries)
    assert any(entry["effect_type"] == "computed" for entry in entries)

    states_payload = json.loads(states_text)
    states = states_payload["states"]
    assert len(states) == 1
    assert states[0]["function_name"] == "flexible_acquisition"
    assert states[0]["parameters"]["triggered_step"] == 4


@pytest.mark.anyio
async def test_finance_get_path_category_series_on_unknown_path_is_a_tool_error(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "path-audit-unknown-path"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=3)
        await _call_ok(session, "core_add_store", plan_name=plan_name, store_name="cash")
        await _call_ok(session, "core_run_path_audit", plan_name=plan_name, num_runs=5, seed=1)

        result = await session.call_tool(
            "finance_get_path_category_series",
            {"plan_name": plan_name, "path": "p99"},
        )

    assert result.isError


@pytest.mark.anyio
async def test_finance_compare_plans_without_results_still_compares_configs(
    server_params: StdioServerParameters,
) -> None:
    """Missing Monte-Carlo results are the expected "not simulated yet" state -
    the comparison must succeed with configuration data only."""
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="compare-a", step_count=3)
        await _call_ok(session, "core_add_store", plan_name="compare-a", store_name="cash")
        await _call_ok(session, "core_create_plan", plan_name="compare-b", step_count=3)
        await _call_ok(session, "core_add_store", plan_name="compare-b", store_name="cash")

        result = await session.call_tool(
            "finance_compare_plans",
            {"plan_name_a": "compare-a", "plan_name_b": "compare-b"},
        )

    assert not result.isError, result.content


@pytest.mark.anyio
async def test_finance_compare_plans_with_corrupted_result_is_a_tool_error(
    server_params: StdioServerParameters, tmp_path: Path
) -> None:
    """A present-but-broken result file is a real error and must propagate,
    not silently degrade into the "no result yet" behavior."""
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="corrupt-a", step_count=3)
        await _call_ok(session, "core_add_store", plan_name="corrupt-a", store_name="cash")
        await _call_ok(session, "core_create_plan", plan_name="corrupt-b", step_count=3)
        await _call_ok(session, "core_add_store", plan_name="corrupt-b", store_name="cash")

        # The server's working directory is tmp_path/"work" (see server_params).
        corrupted = tmp_path / "work" / "corrupt-a" / "monte_carlo_result.json"
        corrupted.write_text("{ this is not valid json", encoding="utf-8")

        result = await session.call_tool(
            "finance_compare_plans",
            {"plan_name_a": "corrupt-a", "plan_name_b": "corrupt-b"},
        )

    assert result.isError


@pytest.mark.anyio
async def test_finance_compare_plan_actuals_with_corrupted_audit_is_a_tool_error(
    server_params: StdioServerParameters, tmp_path: Path
) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name="actuals-corrupt", step_count=3)
        await _call_ok(session, "core_add_store", plan_name="actuals-corrupt", store_name="cash")

        # Regression: with no audit result at all, the tool degrades gracefully.
        missing_ok = await session.call_tool(
            "finance_compare_plan_actuals",
            {"plan_name": "actuals-corrupt", "current_step": 0},
        )
        assert not missing_ok.isError, missing_ok.content

        corrupted = tmp_path / "work" / "actuals-corrupt" / "path_audit_result.json"
        corrupted.write_text('{"paths": "wrong-shape"}', encoding="utf-8")

        result = await session.call_tool(
            "finance_compare_plan_actuals",
            {"plan_name": "actuals-corrupt", "current_step": 0},
        )

    assert result.isError


@pytest.mark.anyio
async def test_finance_get_path_event_log_without_a_path_audit_is_a_tool_error(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "path-audit-missing"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=3)
        await _call_ok(session, "core_add_store", plan_name=plan_name, store_name="cash")

        result = await session.call_tool(
            "finance_get_path_event_log",
            {"plan_name": plan_name, "path": "deterministic"},
        )

    assert result.isError
