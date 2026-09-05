"""Tidy the raw text before it gets typed.

Two layers:
  rules  - free, instant, no internet. Always runs.
  llm    - Claude reads it and rewrites it properly. Optional, needs a key.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol


class Cleaner(Protocol):
    name: str

    def clean(self, text: str, terms: Sequence[str] = ()) -> str:
        """Tidy the text. `terms` are your own words, spelled correctly."""


class NoCleaner:
    name = "none"

    def clean(self, text: str, terms: Sequence[str] = ()) -> str:
        return text


def build(settings: dict[str, Any]) -> Cleaner:
    mode = settings.get("mode", "rules")
    if mode == "none":
        return NoCleaner()
    if mode == "rules":
        from .rules import RulesCleaner

        return RulesCleaner(remove_repeats=bool(settings.get("remove_repeats", False)))
    if mode == "llm":
        from .llm import ClaudeCleaner

        return ClaudeCleaner(settings.get("llm", {}))
    raise ValueError(f"Unknown cleanup mode: {mode!r}")
