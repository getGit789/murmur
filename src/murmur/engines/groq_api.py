"""Cloud speech to text through Groq. Fast. Needs GROQ_API_KEY.

The network can drop. Rather than lose what you just said, a failed
call is tried once more, and then handed to the local model.
"""

from __future__ import annotations

import io
import os
import time
import wave
from typing import Any

import httpx
import numpy as np

from .. import config

ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"


def to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())
    return buffer.getvalue()


def key_path():
    """The key file, next to your settings."""
    return config.config_dir() / "groq.key"


def read_key() -> str:
    """The GROQ_API_KEY variable first, then the key file.

    The file matters: a variable set with setx only reaches programs
    started afterwards, so a fresh key would not be seen until you log
    out. The file works straight away and after every reboot.
    """
    from_environment = os.environ.get("GROQ_API_KEY", "").strip()
    if from_environment:
        return from_environment
    path = key_path()
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


class GroqWhisper:
    name = "groq"

    def __init__(
        self, settings: dict[str, Any], fallback: dict[str, Any] | None = None
    ) -> None:
        self._model = settings.get("model", "whisper-large-v3-turbo")
        self._api_key = read_key()
        # Only built if the network lets us down, so it costs nothing today.
        self._fallback_settings = fallback or {}
        self._fallback = None

    def warm_up(self) -> None:
        if not self._api_key:
            raise RuntimeError(
                f"No Groq key. Put it in {key_path()}, set GROQ_API_KEY, "
                'or use backend = "local".'
            )
        print(f"[engine] groq ready ({self._model})")

    def _ask_groq(self, audio: np.ndarray, sample_rate: int, prompt: str) -> str:
        files = {"file": ("clip.wav", to_wav_bytes(audio, sample_rate), "audio/wav")}
        data = {
            "model": self._model,
            "response_format": "json",
            # Saying the language stops it guessing, and stops it translating.
            "language": "en",
            # No creativity. We want what was said, not something plausible.
            "temperature": "0",
        }
        if prompt:
            data["prompt"] = prompt
        response = httpx.post(
            ENDPOINT,
            headers={"Authorization": f"Bearer {self._api_key}"},
            files=files,
            data=data,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json().get("text", "").strip()

    def _local_engine(self):
        """Built the first time the cloud lets us down, then kept."""
        if self._fallback is None:
            from .local_whisper import LocalWhisper

            print("[engine] building the local stand in ...")
            self._fallback = LocalWhisper(self._fallback_settings)
        return self._fallback

    def transcribe(self, audio: np.ndarray, sample_rate: int, prompt: str = "") -> str:
        problem: Exception | None = None
        for attempt in (1, 2):
            try:
                return self._ask_groq(audio, sample_rate, prompt)
            except Exception as error:  # network blip, rate limit, timeout
                problem = error
                print(f"[engine] groq attempt {attempt} failed: {error}")
                if attempt == 1:
                    time.sleep(0.4)

        print(f"[engine] groq unreachable ({problem}). Using the local model.")
        return self._local_engine().transcribe(audio, sample_rate, prompt)
