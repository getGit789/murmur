"""Claude rewrites the raw text: fillers out, grammar fixed, meaning kept.

Falls back to the rules cleaner if anything goes wrong. Your words are
never lost, even with no internet.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .rules import RulesCleaner

SYSTEM = """You clean up raw voice dictation before it is typed into an app.

Rules:
- Return ONLY the cleaned text. No preamble, no quotes, no explanation.
- Keep the speaker's meaning, words, and tone. Do not add new ideas.
- Remove filler ("um", "uh", "you know") and false starts.
- If the speaker corrects themselves, keep only the corrected version.
- Fix punctuation, capitals, and obvious grammar slips.
- Keep it the same length or shorter. Never expand or embellish.
- If the text is already clean, return it unchanged.
- If the text is a fragment, leave it a fragment. Do not invent an ending."""


class ClaudeCleaner:
    name = "llm"

    def __init__(self, settings: dict[str, Any]) -> None:
        self._model = settings.get("model", "claude-opus-5")
        self._effort = settings.get("effort", "low")
        self._timeout = float(settings.get("timeout_seconds", 8))
        self._max_tokens = int(settings.get("max_tokens", 4096))
        self._fallback = RulesCleaner()
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(timeout=self._timeout, max_retries=1)
        return self._client

    def clean(self, text: str, terms: Sequence[str] = ()) -> str:
        if not text.strip():
            return text
        safe = self._fallback.clean(text, terms)

        system = SYSTEM
        if terms:
            system += (
                "\n\nSpell these the user's way when they come up: "
                + ", ".join(terms)
                + "."
            )

        try:
            response = self._get_client().beta.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system,
                thinking={"type": "adaptive"},
                output_config={"effort": self._effort},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                messages=[{"role": "user", "content": text}],
            )
        except Exception as error:
            print(f"[cleanup] Claude call failed ({error}). Using rules instead.")
            return safe

        if response.stop_reason == "refusal":
            print("[cleanup] Claude declined. Using rules instead.")
            return safe

        parts = [b.text for b in response.content if b.type == "text"]
        result = "".join(parts).strip()
        return result or safe
