from pathlib import Path

import pytest

from compute_to_ai.mcp.settings import (
    SETTINGS_PATH_ENV_VAR,
    default_settings_path,
    load_settings,
    resolve_settings_path,
)


def test_load_settings_keeps_absolute_working_directory(tmp_path: Path) -> None:
    working_directory = tmp_path / "work"
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text(
        f'working_directory = "{working_directory.as_posix()}"\n', encoding="utf-8"
    )

    settings = load_settings(settings_file)

    assert settings.working_directory == working_directory
    assert settings.logging.level == "INFO"


def test_load_settings_resolves_relative_working_directory_against_settings_file(
    tmp_path: Path,
) -> None:
    settings_file = tmp_path / "settings.toml"
    settings_file.write_text('working_directory = "./work"\n', encoding="utf-8")

    settings = load_settings(settings_file)

    assert settings.working_directory == (tmp_path / "work").resolve()


def test_resolve_settings_path_uses_env_var_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    override = tmp_path / "custom-settings.toml"
    monkeypatch.setenv(SETTINGS_PATH_ENV_VAR, str(override))

    assert resolve_settings_path() == override


def test_resolve_settings_path_falls_back_to_platform_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(SETTINGS_PATH_ENV_VAR, raising=False)

    assert resolve_settings_path() == default_settings_path()
