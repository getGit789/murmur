"""Local speech to text. Runs on the CPU. No internet, nothing leaves the PC."""

from __future__ import annotations

from typing import Any

import numpy as np


class LocalWhisper:
    name = "local"

    def __init__(self, settings: dict[str, Any]) -> None:
        self._model_size = settings.get("model", "base.en")
        self._compute_type = settings.get("compute_type", "int8")
        self._cpu_threads = int(settings.get("cpu_threads", 6))
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            print(f"[engine] loading local model {self._model_size} ...")
            self._model = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type=self._compute_type,
                cpu_threads=self._cpu_threads,
            )
        return self._model

    def warm_up(self) -> None:
        model = self._ensure_model()
        silence = np.zeros(16000, dtype=np.float32)
        list(model.transcribe(silence, beam_size=1)[0])
        print("[engine] local model ready")

    def transcribe(self, audio: np.ndarray, sample_rate: int, prompt: str = "") -> str:
        del sample_rate  # faster-whisper expects 16 kHz, which is what we record
        model = self._ensure_model()
        segments, _info = model.transcribe(
            audio,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            initial_prompt=prompt or None,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()
