"""Quality Gate & Code Architecture enforcement tests.

Enforces project structure conventions, including maximum line limits per module
(max 500 lines per file in src/).
"""

from pathlib import Path

MAX_MODULE_LINES = 500


def test_no_source_file_exceeds_line_limit() -> None:
    """Quality Gate: Ensures no Python module in src/ exceeds MAX_MODULE_LINES (500 lines)."""
    src_dir = Path("src/compute_to_ai")
    too_long_files: list[str] = []

    for py_file in sorted(src_dir.rglob("*.py")):
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        if lines > MAX_MODULE_LINES:
            too_long_files.append(
                f"{py_file.relative_to(src_dir)}: {lines} lines (limit: {MAX_MODULE_LINES})"
            )

    assert not too_long_files, (
        f"The following {len(too_long_files)} source files exceed the {MAX_MODULE_LINES}-line "
        "limit and must be modularized into domain sub-modules:\n"
        + "\n".join(f"  - {item}" for item in too_long_files)
    )
