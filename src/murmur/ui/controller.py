"""Glue. The engine below is untouched; this only drives it and reports up.

Recording and transcribing happen off the UI thread, so the window and the
meter never stutter.
"""

from __future__ import annotations

import threading
import time
import traceback

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

from .. import cleanup, config, engines, inject
from ..audio import Recorder
from ..dictionary import Dictionary
from ..history import Applied, Entry, History

try:
    import winsound
except ImportError:
    winsound = None


class Controller(QObject):
    """Owns the engine. Emits plain signals the UI can connect to."""

    state_changed = Signal(str, str)      # state, human text
    level_changed = Signal(float)
    seconds_changed = Signal(float)
    entry_added = Signal(object)          # history.Entry
    engine_ready = Signal(str)

    def __init__(self, history: History, dictionary: Dictionary) -> None:
        super().__init__()
        self.settings = config.load()
        self.history = history
        self.dictionary = dictionary

        self.sample_rate = int(self.settings["audio"]["sample_rate"])
        self.min_seconds = float(self.settings["audio"]["min_seconds"])
        self.min_level = float(self.settings["audio"].get("min_level", 0.006))
        self.beep_on = bool(self.settings["feedback"].get("beep", True))

        self.recorder = Recorder(self.sample_rate)
        self.engine = engines.build(self.settings["engine"])
        self.cleaner = cleanup.build(self.settings["cleanup"])

        self._busy = threading.Lock()
        self._elapsed = 0.0
        self._ready = False

        self._meter = QTimer(self)
        self._meter.timeout.connect(self._pump)
        self._meter.start(33)

    # ---- lifecycle ------------------------------------------------------

    def warm_up(self) -> None:
        self.state_changed.emit("working", "Warming up")

        def work() -> None:
            try:
                self.engine.warm_up()
                self._ready = True
                name = f"{self.engine.name} · {self.cleaner.name}"
                self.engine_ready.emit(name)
                self.state_changed.emit("idle", "Ready")
            except Exception as error:
                traceback.print_exc()
                self.state_changed.emit("error", str(error)[:60])

        threading.Thread(target=work, daemon=True).start()

    def reload_dictionary(self) -> None:
        self.dictionary = Dictionary.load()

    def reload_engine(self) -> None:
        """Rebuild the engine after a settings change, then warm it up.

        Used when Fast Mode is switched on, so the new key and backend
        take effect without restarting the app.
        """
        self.settings = config.load()
        self.engine = engines.build(self.settings["engine"])
        self.warm_up()

    # ---- transport ------------------------------------------------------

    @property
    def is_recording(self) -> bool:
        return self.recorder.is_recording

    def start(self) -> None:
        if self.recorder.is_recording:
            return
        self.recorder.start()
        self._elapsed = 0.0
        self.state_changed.emit("recording", "Recording")
        self._beep(880)

    def stop(self) -> None:
        if not self.recorder.is_recording:
            return
        audio = self.recorder.stop()
        self._beep(660)
        threading.Thread(target=self._process, args=(audio,), daemon=True).start()

    def toggle(self) -> None:
        self.stop() if self.recorder.is_recording else self.start()

    # ---- the slow part --------------------------------------------------

    def _process(self, audio: np.ndarray) -> None:
        seconds = len(audio) / self.sample_rate
        if seconds < self.min_seconds:
            self.state_changed.emit("idle", "Too short")
            return

        loudness = float(np.sqrt(np.mean(np.square(audio)))) if len(audio) else 0.0
        if loudness < self.min_level:
            self.state_changed.emit("idle", "Too quiet")
            return

        with self._busy:
            self.state_changed.emit("working", "Transcribing")
            started = time.monotonic()
            try:
                # MECHANISM 1: bias the engine before it transcribes.
                raw = self.engine.transcribe(
                    audio, self.sample_rate, prompt=self.dictionary.bias_prompt()
                )
                print(
                    f"[engine] {self.engine.name}: {seconds:.1f}s of speech "
                    f"in {time.monotonic() - started:.2f}s"
                )
            except Exception:
                traceback.print_exc()
                self.state_changed.emit("error", "Transcribe failed")
                return

            if engines.is_invented(raw):
                # Silence or a noise the model turned into a subtitle.
                self.state_changed.emit("idle", "Nothing heard")
                return

            # MECHANISM 2: the correction pass afterwards.
            text, applied = self.dictionary.apply(raw)

            try:
                text = self.cleaner.clean(text, self.dictionary.terms)
            except Exception:
                traceback.print_exc()

            if not text.strip():
                self.state_changed.emit("idle", "Nothing heard")
                return

            inject.type_text(
                text,
                mode=self.settings["output"]["mode"],
                trailing_space=bool(self.settings["output"]["trailing_space"]),
            )

            entry = Entry(
                raw=raw,
                final=text,
                seconds=seconds,
                engine=self.engine.name,
                corrections=[
                    Applied(heard=a.heard, written=a.written, count=a.count)
                    for a in applied
                ],
            )
            self.history.add(entry)
            self.entry_added.emit(entry)

            fired = f"  ({len(applied)} fixed)" if applied else ""
            preview = text if len(text) <= 46 else text[:43] + "..."
            self.state_changed.emit("idle", f"{preview}{fired}")

    # ---- meter ----------------------------------------------------------

    def _pump(self) -> None:
        self.level_changed.emit(self.recorder.level)
        if self.recorder.is_recording:
            self._elapsed += 0.033
            self.seconds_changed.emit(self._elapsed)

    def _beep(self, frequency: int) -> None:
        if self.beep_on and winsound is not None:
            try:
                winsound.Beep(frequency, 60)
            except RuntimeError:
                pass

    def shutdown(self) -> None:
        self._meter.stop()
        if self.recorder.is_recording:
            self.recorder.stop()
