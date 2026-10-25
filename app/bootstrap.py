"""Load application runtime configuration from the environment safely."""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dotenv import dotenv_values

from app.config import load_config

if TYPE_CHECKING:
    from app.config import AppConfig

_MAX_DOTENV_BYTES = 100 * 1024
_DOTENV_ERROR = "Unable to load runtime environment file"


def _environment_copy(env: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a private copy of the caller's environment."""
    if env is None:
        return dict(os.environ)
    return dict(env)


def _read_dotenv(path: Path) -> dict[str, Any]:
    """Read an optional .env file without interpolating or logging values."""
    try:
        file_stat = path.lstat()
    except FileNotFoundError:
        return {}
    except OSError:
        raise ValueError(_DOTENV_ERROR) from None

    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise ValueError(_DOTENV_ERROR)
    if file_stat.st_size > _MAX_DOTENV_BYTES:
        raise ValueError(_DOTENV_ERROR)

    try:
        parsed = dotenv_values(path, interpolate=False)
    except Exception:
        raise ValueError(_DOTENV_ERROR) from None

    return {key: value for key, value in parsed.items() if value is not None}


def load_runtime_config(
    project_root: Path,
    *,
    demo: bool = False,
    env: Mapping[str, Any] | None = None,
) -> AppConfig:
    """Load runtime configuration, optionally bypassing .env for demo mode."""
    root = Path(project_root)
    config_path = root / "config" / "local.toml"
    environment = _environment_copy(env)

    if demo:
        environment.pop("OPENROUTER_API_KEY", None)
        environment.pop("APP_LLM_MODEL", None)
        environment["APP_LLM_ENABLED"] = "false"
        return load_config(environment, config_path)

    merged = _read_dotenv(root / ".env")
    merged.update(environment)
    return load_config(merged, config_path)
