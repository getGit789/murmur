"""Put the text into whatever window has focus."""

from __future__ import annotations

import time

import pyperclip
from pynput import keyboard

_controller = keyboard.Controller()

# Slow apps (Electron, some terminals) read the clipboard a moment after
# Ctrl+V. Restoring the old clipboard too early hands them the OLD
# content, so the user sees stale text instead of the transcript.
RESTORE_AFTER = 0.6


def _paste() -> None:
    _controller.press(keyboard.Key.ctrl)
    _controller.press("v")
    _controller.release("v")
    _controller.release(keyboard.Key.ctrl)


def type_text(text: str, mode: str = "paste", trailing_space: bool = True) -> None:
    """Send text to the focused app. Paste is fast; type is slower but safer."""
    if not text:
        return
    payload = text + (" " if trailing_space else "")

    if mode == "type":
        _controller.type(payload)
        return

    # Paste mode: borrow the clipboard, then give it back.
    try:
        saved = pyperclip.paste()
    except Exception:  # clipboard can be empty or locked by another app
        saved = ""

    # Make sure the payload really landed. Another app can hold the
    # clipboard for a moment; pasting before it lands sends old content.
    landed = False
    for _ in range(6):
        try:
            pyperclip.copy(payload)
            time.sleep(0.02)
            if pyperclip.paste() == payload:
                landed = True
                break
        except Exception:
            time.sleep(0.05)
    if not landed:
        # Do not paste whatever happens to be in the clipboard.
        _controller.type(payload)
        return

    _paste()
    time.sleep(RESTORE_AFTER)

    # Give the old clipboard back, unless something else claimed it since.
    try:
        if pyperclip.paste() == payload:
            pyperclip.copy(saved)
    except Exception:
        pass
