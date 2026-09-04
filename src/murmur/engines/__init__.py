"""Speech to text back ends. Swap one for the other in config.toml."""

from __future__ import annotations

import re
from typing import Any, Protocol

import numpy as np


# These models were trained on video subtitles, so on a cough, a door, or a
# breath they sometimes write a caption instead of nothing. A clip whose
# whole result is one of these is thrown away rather than typed.
INVENTED = {
    "thanks for watching",
    "thank you for watching",
    "thanks for watching everyone",
    "please subscribe",
    "subscribe to my channel",
    "like and subscribe",
    "see you next time",
    "music",
    "applause",
    "laughter",
    "silence",
    "foreign",
    "outro music",
    "background music",
}


def is_invented(text: str) -> bool:
    """True when the result is a subtitle artefact, not something you said."""
    bare = re.sub(r"[^\w\s]", " ", text).strip().lower()
    bare = re.sub(r"\s+", " ", bare)
    return not bare or bare in INVENTED


class Transcriber(Protocol):
    """Every back end looks the same to the app."""

    name: str

    def warm_up(self) -> None:
        """Load the model early so the first press is not slow."""

    def transcribe(self, audio: np.ndarray, sample_rate: int, prompt: str = "") -> str:
        """Turn audio into text. `prompt` nudges it toward your own words."""


def build(settings: dict[str, Any]) -> Transcriber:
    backend = settings.get("backend", "local")
    if backend == "local":
        from .local_whisper import LocalWhisper

        return LocalWhisper(settings.get("local", {}))
    if backend == "groq":
        from .groq_api import GroqWhisper

        # The local settings ride along as the stand in for a dropped network.
        return GroqWhisper(settings.get("groq", {}), settings.get("local", {}))
    raise ValueError(f"Unknown engine backend: {backend!r}")
