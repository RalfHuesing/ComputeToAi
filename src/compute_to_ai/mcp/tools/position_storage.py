"""Position registry JSON file storage, persisted next to plan.json.

See "Arbeitsverzeichnis" in Docs/02-Architektur-und-MCP.md.
"""

from pathlib import Path

from compute_to_ai.features.finance.position import PositionRegistry
from compute_to_ai.mcp.tools.plan_storage import result_file, save_result

POSITION_REGISTRY_FILENAME = "positions.json"


def load_position_registry(working_directory: Path, plan_name: str) -> PositionRegistry:
    """Load a plan's position registry, or a fresh empty one if none exists yet.

    Unlike a Monte-Carlo/path-audit result, there's no required prior action
    before this file can meaningfully be absent - a plan with no live-price
    tracked positions yet is a normal state, not an error.
    """
    file = result_file(working_directory, plan_name, POSITION_REGISTRY_FILENAME)
    if not file.exists():
        return PositionRegistry()
    return PositionRegistry.model_validate_json(file.read_text(encoding="utf-8"))


def save_position_registry(
    working_directory: Path, plan_name: str, registry: PositionRegistry
) -> None:
    save_result(working_directory, plan_name, POSITION_REGISTRY_FILENAME, registry)
