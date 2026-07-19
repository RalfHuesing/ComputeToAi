"""Tests for position_storage.py - load/save round-trip of the position registry."""

from pathlib import Path

from compute_to_ai.features.finance.position import PositionMetadata, PositionRegistry
from compute_to_ai.mcp.tools.position_storage import (
    load_position_registry,
    save_position_registry,
)


def test_load_position_registry_returns_empty_registry_when_file_missing(tmp_path: Path) -> None:
    registry = load_position_registry(tmp_path, "some-plan")

    assert registry == PositionRegistry()


def test_save_and_load_position_registry_round_trip(tmp_path: Path) -> None:
    registry = PositionRegistry(
        positions={
            "equity": PositionMetadata(
                isin_or_wkn="LU2572257124",
                shares=10.0,
                exchange="Xetra",
                last_updated="2026-07-19T00:00:00+00:00",
            )
        }
    )

    save_position_registry(tmp_path, "some-plan", registry)
    loaded = load_position_registry(tmp_path, "some-plan")

    assert loaded == registry
