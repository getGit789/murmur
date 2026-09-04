"""Keep a log file.

The built app has no console window, so without this you could never see
why something went wrong. Everything printed also lands in the log.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from . import config

MAX_BYTES = 512_000  # keep the file small; older lines get rolled off


def log_path() -> Path:
    return config.config_dir() / "murmur.log"


class _Tee:
    """Writes to the console (if there is one) and to the log file."""

    def __init__(self, stream, handle) -> None:
        self._stream = stream
        self._handle = handle

    def write(self, text: str) -> int:
        if self._stream is not None:
            try:
                self._stream.write(text)
            except Exception:
                pass
        try:
            self._handle.write(text)
            self._handle.flush()
        except Exception:
            pass
        return len(text)

    def flush(self) -> None:
        for target in (self._stream, self._handle):
            try:
                if target is not None:
                    target.flush()
            except Exception:
                pass

    def isatty(self) -> bool:
        return bool(self._stream and getattr(self._stream, "isatty", lambda: False)())


def start() -> Path:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > MAX_BYTES:
        path.unlink()

    handle = path.open("a", encoding="utf-8", errors="replace")
    handle.write(f"\n===== started {datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
    handle.flush()

    sys.stdout = _Tee(sys.stdout, handle)
    sys.stderr = _Tee(sys.stderr, handle)
    return path
