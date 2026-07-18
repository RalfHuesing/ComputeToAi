"""Shared Plan/result JSON file storage for MCP tools.

See "Arbeitsverzeichnis" in Docs/02-Architektur-und-MCP.md.
"""

from pathlib import Path

from pydantic import BaseModel

from compute_to_ai.engine.plan import Plan


def plan_file(working_directory: Path, plan_name: str) -> Path:
    return working_directory / plan_name / "plan.json"


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
        raise ValueError(msg)
    return model.model_validate_json(file.read_text(encoding="utf-8"))


def save_result(working_directory: Path, plan_name: str, filename: str, result: BaseModel) -> None:
    file = result_file(working_directory, plan_name, filename)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
