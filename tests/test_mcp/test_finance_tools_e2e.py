"""End-to-end test over the real stdio transport for the finance_* tools.

Builds the "Anna" example plan from Docs/10-Roadmap.md purely through MCP
tool calls (not the engine's Python API) and runs a Monte-Carlo simulation
on it, proving the full pipeline of building blocks composes correctly
through the real MCP surface. Individual building blocks already have
hand-calculated golden tests in tests/test_features/test_finance/ - this
test is deliberately integration-level, not a golden-value check, since a
Monte-Carlo result has no closed-form expected value.
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
async def test_anna_example_plan_end_to_end(server_params: StdioServerParameters) -> None:
    """Anna, 20, salary + expenses, car loan, mortgage, portfolio, cash bucket,
    taxes, and statutory pension - built entirely via finance_* MCP tool calls,
    then a Monte-Carlo run over the full plan (Docs/10-Roadmap.md, "Anna")."""
    plan_name = "anna"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        # 20 to 90 years old, yearly steps.
        await _call_ok(
            session, "core_create_plan", plan_name=plan_name, step_count=70, steps_per_year=1
        )
        await _call_ok(session, "core_add_store", plan_name=plan_name, store_name="cash")

        await _call_ok(
            session,
            "finance_set_life_phases",
            plan_name=plan_name,
            current_age=20,
            employment_end_age=63,
            statutory_pension_start_age=67,
            life_expectancy_age=90,
        )

        await _call_ok(
            session,
            "finance_add_income_stream",
            plan_name=plan_name,
            name="Gehalt",
            store_name="cash",
            amount=33600.0,
            growth_rate=0.02,
            active_phases=["Erwerbsphase"],
            frequency="yearly",
        )
        await _call_ok(
            session,
            "finance_add_expense",
            plan_name=plan_name,
            name="Lebenshaltung",
            store_name="cash",
            amount=19200.0,
            inflation_rate=0.02,
            frequency="yearly",
        )

        # Car loan at 25 (step 5): 20,000 EUR, 4%, ~5-year annual payment.
        await _call_ok(
            session,
            "finance_add_liability",
            plan_name=plan_name,
            name="Autokredit",
            liability_store_name="autokredit",
            cash_store_name="cash",
            principal=20000.0,
            interest_rate=0.04,
            payment=4493.35,
            start_step=5,
            end_step=9,
        )

        # House at 28 (step 8): 70,000 EUR down payment (fixed acquisition from cash),
        # 280,000 EUR mortgage, 3.5%, ~25-year annual payment.
        await _call_ok(
            session,
            "finance_add_fixed_acquisition",
            plan_name=plan_name,
            name="Eigenkapital Haus",
            store_name="cash",
            amount=70000.0,
            step=8,
        )
        await _call_ok(
            session,
            "finance_add_liability",
            plan_name=plan_name,
            name="Hypothek",
            liability_store_name="hypothek",
            cash_store_name="cash",
            principal=280000.0,
            interest_rate=0.035,
            payment=16826.0,
            start_step=8,
            end_step=32,
        )

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
            "finance_set_correlation_matrix",
            plan_name=plan_name,
            group_name="portfolio",
            matrix=[[1.0, -0.2], [-0.2, 1.0]],
            store_names=["equity", "bond"],
        )

        await _call_ok(
            session,
            "finance_add_cash_bucket",
            plan_name=plan_name,
            portfolio_weights={"equity": 0.70, "bond": 0.30},
            emergency_buffer_months={"Erwerbsphase": 6.0, "Frühruhestandslücke": 6.0},
            monthly_expenses=1600.0,
            inflation_rate=0.02,
            withdrawal_years=3.0,
            withdrawal_phase_names=["Frühruhestandslücke", "Rentenphase"],
        )

        await _call_ok(
            session,
            "finance_add_tax_manager",
            plan_name=plan_name,
            asset_classes={
                "equity": {
                    "partial_exemption_rate": 0.30,
                    "is_accumulating": True,
                    "growth_rate": 0.07,
                },
                "bond": {
                    "partial_exemption_rate": 0.0,
                    "is_accumulating": True,
                    "growth_rate": 0.03,
                },
            },
            retirement_step=47,
        )

        await _call_ok(
            session,
            "finance_add_statutory_pension",
            plan_name=plan_name,
            name="Rente",
            store_name="cash",
            annual_amount_at_regular_retirement_age=21600.0,
            regular_retirement_step=47,
            actual_retirement_step=47,
            annual_increase_rate=0.01,
            active_phases=["Rentenphase"],
        )

        await _call_ok(
            session,
            "finance_set_target_condition",
            plan_name=plan_name,
            ruin_stores=["cash", "equity", "bond"],
            ruin_threshold=0.0,
        )

        await _call_ok(
            session, "finance_run_monte_carlo", plan_name=plan_name, num_runs=50, seed=42
        )
        result_text = await _call_ok(session, "finance_get_monte_carlo_result", plan_name=plan_name)

    payload = json.loads(result_text)
    assert payload["num_runs"] == 50
    assert 0.0 <= payload["ruin_probability"] <= 1.0
    assert set(payload["final_balances_percentiles"]) == {
        "cash",
        "equity",
        "bond",
        "autokredit",
        "hypothek",
    }
    assert "raw_final_balances" not in payload


@pytest.mark.anyio
async def test_finance_add_income_stream_on_unknown_plan_is_a_tool_error(
    server_params: StdioServerParameters,
) -> None:
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool(
            "finance_add_income_stream",
            {
                "plan_name": "does-not-exist",
                "name": "Gehalt",
                "store_name": "cash",
                "amount": 1000.0,
            },
        )

    assert result.isError


@pytest.mark.anyio
async def test_finance_add_income_stream_rejects_unknown_phase_name(
    server_params: StdioServerParameters,
) -> None:
    plan_name = "phase-validation-test"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=10)
        await _call_ok(session, "core_add_store", plan_name=plan_name, store_name="cash")
        await _call_ok(
            session,
            "finance_set_life_phases",
            plan_name=plan_name,
            current_age=20,
            employment_end_age=63,
            statutory_pension_start_age=67,
            life_expectancy_age=90,
        )

        result = await session.call_tool(
            "finance_add_income_stream",
            {
                "plan_name": plan_name,
                "name": "Gehalt",
                "store_name": "cash",
                "amount": 1000.0,
                "active_phases": ["work"],
            },
        )

    assert result.isError


@pytest.mark.anyio
async def test_add_tools_echo_stored_values(server_params: StdioServerParameters) -> None:
    """Mutating add_* tools must echo the actually stored, converted values -
    e.g. the frequency-folded amount_per_step and the pension amount after
    Rentenabschlag - so the caller can verify them against its own input."""
    plan_name = "structured-echo-test"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _call_ok(
            session, "core_create_plan", plan_name=plan_name, step_count=50, steps_per_year=1
        )
        await _call_ok(session, "core_add_store", plan_name=plan_name, store_name="cash")

        income_text = await _call_ok(
            session,
            "finance_add_income_stream",
            plan_name=plan_name,
            name="Gehalt",
            store_name="cash",
            amount=1000.0,
            frequency="monthly",
        )
        income = json.loads(income_text)
        # "monthly" on an annual-step plan folds 12 occurrences into one step.
        assert income["amount_per_step"] == pytest.approx(12000.0)
        assert income["interval_steps"] == 1
        assert income["name"] == "Gehalt"
        assert income["store_name"] == "cash"

        # The echo matches what is actually stored in the plan.
        effects_text = await _call_ok(session, "core_list_effects", plan_name=plan_name)
        stored = next(
            effect
            for effect in json.loads(effects_text)["effects"]
            if effect["name"] == "Gehalt"
        )
        assert stored["amount_per_step"] == pytest.approx(income["amount_per_step"])

        pension_text = await _call_ok(
            session,
            "finance_add_statutory_pension",
            plan_name=plan_name,
            name="Rente",
            store_name="cash",
            annual_amount_at_regular_retirement_age=12000.0,
            regular_retirement_step=47,
            actual_retirement_step=43,
        )
        pension = json.loads(pension_text)
        # 4 years early -> capped 14.4% reduction -> factor 0.856.
        assert pension["annual_amount"] == pytest.approx(12000.0 * 0.856)
        assert pension["adjustment_factor"] == pytest.approx(0.856)
        assert pension["start_step"] == 43


@pytest.mark.anyio
async def test_finance_set_life_phases_scales_with_steps_per_year(
    server_params: StdioServerParameters,
) -> None:
    """On a monthly-step plan, the same ages must yield monthly phase boundaries."""
    plan_name = "monthly-phases-test"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _call_ok(
            session, "core_create_plan", plan_name=plan_name, step_count=720, steps_per_year=12
        )
        await _call_ok(
            session,
            "finance_set_life_phases",
            plan_name=plan_name,
            current_age=30,
            employment_end_age=67,
            statutory_pension_start_age=67,
            life_expectancy_age=90,
        )
        phases_text = await _call_ok(session, "core_list_phases", plan_name=plan_name)

    payload = json.loads(phases_text)
    boundaries = [(p["name"], p["start_step"], p["end_step"]) for p in payload["phases"]]
    assert boundaries == [
        ("Erwerbsphase", 0, (67 - 30) * 12),
        ("Rentenphase", (67 - 30) * 12, (90 - 30) * 12),
    ]


@pytest.mark.anyio
async def test_finance_calculate_pension_adjustment_needs_no_plan(
    server_params: StdioServerParameters,
) -> None:
    """A stateless quick-check for "what if I retire 5 years early?" -
    4 years early (48 months) means the 14.4% cap applies (Docs/09)."""
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result_text = await _call_ok(
            session,
            "finance_calculate_pension_adjustment",
            base_amount=1800.0,
            months_early=48,
        )

    assert pytest.approx(float(result_text)) == 1800.0 * 0.856


@pytest.mark.anyio
async def test_finance_add_expense_frequency_e2e(
    server_params: StdioServerParameters,
) -> None:
    """Verify finance_add_expense and finance_add_income_stream accept frequency parameters."""
    plan_name = "freq_test_plan"
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await _call_ok(session, "core_create_plan", plan_name=plan_name, step_count=24)
        await _call_ok(
            session,
            "core_add_store",
            plan_name=plan_name,
            store_name="cash",
            initial_balance=10000.0,
        )

        await _call_ok(
            session,
            "finance_add_expense",
            plan_name=plan_name,
            name="KFZ-Versicherung",
            store_name="cash",
            amount=1200.0,
            frequency="yearly",
        )
        await _call_ok(
            session,
            "finance_add_income_stream",
            plan_name=plan_name,
            name="Bonus",
            store_name="cash",
            amount=5000.0,
            frequency="every_n_years",
            interval_years=2,
        )

        res_text = await _call_ok(session, "core_run_simulation", plan_name=plan_name, runs=1)
        assert "freq_test_plan" in res_text

