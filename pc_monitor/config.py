from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PORT = 5000
DEFAULT_REFRESH_SECONDS = 2


@dataclass(slots=True)
class AppConfig:
    port: int = DEFAULT_PORT
    refresh_seconds: int = DEFAULT_REFRESH_SECONDS


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return get_project_root()


def get_bundle_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return get_project_root()


def get_config_path() -> Path:
    return get_runtime_root() / "config.json"


def get_template_dir() -> Path:
    return get_bundle_root() / "pc_monitor" / "templates"


def get_static_dir() -> Path:
    return get_bundle_root() / "pc_monitor" / "static"


def load_config() -> AppConfig:
    config_data: dict[str, object] = {}
    config_path = get_config_path()

    if config_path.exists():
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            config_data = {}

    return AppConfig(
        port=_normalize_port(config_data.get("port", DEFAULT_PORT)),
        refresh_seconds=_normalize_refresh_seconds(
            config_data.get("refresh_seconds", DEFAULT_REFRESH_SECONDS)
        ),
    )


def _normalize_port(value: object) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return DEFAULT_PORT

    if 1 <= port <= 65535:
        return port
    return DEFAULT_PORT


def _normalize_refresh_seconds(value: object) -> int:
    try:
        refresh_seconds = int(value)
    except (TypeError, ValueError):
        return DEFAULT_REFRESH_SECONDS

    return min(max(refresh_seconds, 1), 30)

