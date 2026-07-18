"""Server bootstrap, stdio transport, logging configuration.

See "Transport", "Logging" and "Selbstbeschreibung" in
Docs/02-Architektur-und-MCP.md.
"""

import logging
import logging.handlers
from collections.abc import Callable
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from platformdirs import user_log_dir

from compute_to_ai.mcp.settings import Settings, load_settings, resolve_settings_path
from compute_to_ai.mcp.tools.calculation_tools import register_calculation_tools
from compute_to_ai.mcp.tools.core_tools import register_core_tools

# Resolved relative to this file, which assumes the server runs from a
# source checkout (see Docs/02-Architektur-und-MCP.md).
DOCS_DIR = Path(__file__).resolve().parents[3] / "Docs"


def _configure_logging(log_directory: Path, level: str) -> None:
    log_directory.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        log_directory / "server.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    package_logger = logging.getLogger("compute_to_ai")
    package_logger.setLevel(level)
    package_logger.addHandler(handler)


def _make_doc_reader(path: Path) -> Callable[[], str]:
    def read_doc() -> str:
        return path.read_text(encoding="utf-8")

    return read_doc


def _register_docs_resources(mcp: FastMCP) -> None:
    if not DOCS_DIR.exists():
        return
    for doc_file in sorted(DOCS_DIR.glob("*.md")):
        mcp.resource(f"docs://{doc_file.name}", name=doc_file.stem, mime_type="text/markdown")(
            _make_doc_reader(doc_file)
        )


def create_server(settings: Settings) -> FastMCP:
    mcp = FastMCP("compute-to-ai")
    register_core_tools(mcp, settings.working_directory)
    register_calculation_tools(mcp)
    _register_docs_resources(mcp)
    return mcp


def main() -> None:
    settings_path = resolve_settings_path()
    try:
        settings = load_settings(settings_path)
    except FileNotFoundError:
        _configure_logging(Path(user_log_dir("compute-to-ai")), "INFO")
        logging.getLogger(__name__).exception("no settings file at %s", settings_path)
        raise

    _configure_logging(settings.working_directory / "logs", settings.logging.level)
    create_server(settings).run(transport="stdio")


if __name__ == "__main__":
    main()
