"""Shared Plan/result JSON file storage for MCP tools.

See "Arbeitsverzeichnis" in Docs/02-Architektur-und-MCP.md.
"""

from pathlib import Path

from pydantic import BaseModel

from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import PathAuditResult, SimulationResult

# Shared across mcp.tools modules (core_tools.py writes it, finance_tools.py
# reads it) so both agree on the same file without duplicating the literal.
PATH_AUDIT_RESULT_FILENAME = "path_audit_result.json"


class ResultNotFoundError(ValueError):
    """A plan has no stored result file yet (simulation not run).

    Distinct from pydantic's ValidationError (also a ValueError subclass) so
    a caller treating "no result yet" as an expected, recoverable state does
    not accidentally swallow a genuinely broken result file with it.
    """


def plan_dir(working_directory: Path, plan_name: str) -> Path:
    return working_directory / plan_name


def plan_file(working_directory: Path, plan_name: str) -> Path:
    return plan_dir(working_directory, plan_name) / "plan.json"


def load_plan(working_directory: Path, plan_name: str) -> Plan:
    file = plan_file(working_directory, plan_name)
    if not file.exists():
        msg = f"no plan named {plan_name!r}; create it first with core_create_plan"
        raise ValueError(msg)
    return Plan.model_validate_json(file.read_text(encoding="utf-8"))


def save_plan(working_directory: Path, plan: Plan) -> None:
    file = plan_file(working_directory, plan.name)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(plan.model_dump_json(indent=2), encoding="utf-8")


def result_file(working_directory: Path, plan_name: str, filename: str) -> Path:
    return working_directory / plan_name / filename


def load_result[ResultT: BaseModel](
    working_directory: Path, plan_name: str, filename: str, model: type[ResultT]
) -> ResultT:
    file = result_file(working_directory, plan_name, filename)
    if not file.exists():
        msg = f"no {filename} for plan {plan_name!r}; run the simulation first"
        raise ResultNotFoundError(msg)
    return model.model_validate_json(file.read_text(encoding="utf-8"))


def save_result(working_directory: Path, plan_name: str, filename: str, result: BaseModel) -> None:
    file = result_file(working_directory, plan_name, filename)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def load_audited_path(working_directory: Path, plan_name: str, path: str) -> SimulationResult:
    """Load one named path (e.g. "p50", "deterministic") from a plan's last
    path audit, or raise ValueError - shared by every core_*/finance_* tool
    that drills into a `core_run_path_audit` result.
    """
    audit = load_result(working_directory, plan_name, PATH_AUDIT_RESULT_FILENAME, PathAuditResult)
    if path not in audit.paths:
        msg = (
            f"no path {path!r} in plan {plan_name!r}'s last path audit "
            f"(run core_run_path_audit first); available paths: {sorted(audit.paths)}"
        )
        raise ValueError(msg)
    return audit.paths[path]
