"""Record the microphone while the key is held down."""

from __future__ import annotations

import queue
import threading

import numpy as np
import sounddevice as sd


class Recorder:
    """Start on key down, stop on key up, give back one audio array."""

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self._chunks: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        # Loudness right now, 0.0 to 1.0. The pill reads this to draw bars.
        self.level = 0.0

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            print(f"[audio] {status}")
        block = indata.copy()
        self._chunks.put(block)
        # Loudness, scaled so normal speech fills most of the bar.
        rms = float(np.sqrt(np.mean(np.square(block))))
        self.level = min(1.0, rms * 12.0)

    def start(self) -> None:
        with self._lock:
            if self._stream is not None:
                return
            while not self._chunks.empty():
                self._chunks.get_nowait()
            self.level = 0.0
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=0,
                callback=self._callback,
            )
            self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop and return mono float32 audio. Empty array if nothing came in."""
        with self._lock:
            stream, self._stream = self._stream, None
        if stream is not None:
            stream.stop()
            stream.close()
        self.level = 0.0

        parts: list[np.ndarray] = []
        while not self._chunks.empty():
            parts.append(self._chunks.get_nowait())
        if not parts:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(parts, axis=0).reshape(-1).astype(np.float32)
