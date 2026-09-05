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
        "remove_repeats": False,
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


def _set_one(text: str, section: str, key: str, value: str) -> str:
    """Replace one key inside one section, leaving comments alone."""
    lines = text.splitlines()
    current = ""
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1]
            continue
        if current == section and stripped.split("=")[0].strip() == key:
            lines[index] = f"{key} = {value}"
            return "\n".join(lines) + "\n"
    if f"[{section}]" not in text:
        lines += ["", f"[{section}]", f"{key} = {value}"]
    else:
        for index, line in enumerate(lines):
            if line.strip() == f"[{section}]":
                lines.insert(index + 1, f"{key} = {value}")
                break
    return "\n".join(lines) + "\n"


def update_values(changes: list[tuple[str, str, str]]) -> None:
    """Write one or more (section, key, toml_value) edits into config.toml.

    Keeps comments and the rest of the file intact. The value must be a
    TOML literal, so a string needs its own quotes: '"groq"'.
    """
    from pathlib import Path as _Path

    path = config_path()
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        example = _Path(__file__).resolve().parents[2] / "config.example.toml"
        text = example.read_text(encoding="utf-8") if example.exists() else ""
    for section, key, value in changes:
        text = _set_one(text, section, key, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
