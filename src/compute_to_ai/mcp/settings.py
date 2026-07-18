"""Settings file loading (TOML -> Pydantic) - see Docs/02-Architektur-und-MCP.md."""

import os
import tomllib
from pathlib import Path

from platformdirs import user_config_dir
from pydantic import BaseModel

SETTINGS_PATH_ENV_VAR = "COMPUTE_TO_AI_SETTINGS"
APP_NAME = "compute-to-ai"


class LoggingSettings(BaseModel):
    level: str = "INFO"


class Settings(BaseModel):
    working_directory: Path
    logging: LoggingSettings = LoggingSettings()


def default_settings_path() -> Path:
    """Platform-appropriate default location, see "Settings-Datei" in Docs/02."""
    return Path(user_config_dir(APP_NAME)) / "settings.toml"


def resolve_settings_path() -> Path:
    """`COMPUTE_TO_AI_SETTINGS` overrides the platform-default settings path."""
    override = os.environ.get(SETTINGS_PATH_ENV_VAR)
    return Path(override) if override else default_settings_path()


def load_settings(path: Path) -> Settings:
    with path.open("rb") as settings_file:
        data = tomllib.load(settings_file)

    settings = Settings.model_validate(data)
    if not settings.working_directory.is_absolute():
        settings.working_directory = (path.parent / settings.working_directory).resolve()
    return settings
