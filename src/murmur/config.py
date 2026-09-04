"""Load settings from %APPDATA%\\Murmur\\config.toml, with safe defaults."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "hotkey": {"key": "ctrl_r"},
    "audio": {"sample_rate": 16000, "min_seconds": 0.35, "min_level": 0.006},
    "engine": {
        "backend": "local",
        "local": {"model": "base.en", "compute_type": "int8", "cpu_threads": 6},
        "groq": {"model": "whisper-large-v3-turbo"},
    },
    "cleanup": {
        "mode": "rules",
        "llm": {
            "model": "claude-opus-5",
            "effort": "low",
            "timeout_seconds": 8,
            "max_tokens": 4096,
        },
    },
    "output": {"mode": "paste", "trailing_space": True},
    "feedback": {"beep": False, "pill": True},
    "startup": {"hidden": False},
}


def config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "Murmur"


def config_path() -> Path:
    return config_dir() / "config.toml"


def _merge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return DEFAULTS
    with path.open("rb") as handle:
        return _merge(DEFAULTS, tomllib.load(handle))
