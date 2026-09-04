"""Listen for one key, anywhere in Windows. Hold = talk."""

from __future__ import annotations

from typing import Callable

from pynput import keyboard

KEY_MAP = {
    "ctrl_r": keyboard.Key.ctrl_r,
    "ctrl_l": keyboard.Key.ctrl_l,
    "alt_r": keyboard.Key.alt_r,
    "alt_l": keyboard.Key.alt_l,
    "caps_lock": keyboard.Key.caps_lock,
    "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10,
    "scroll_lock": keyboard.Key.scroll_lock,
}

FRIENDLY = {
    "ctrl_r": "Right Ctrl",
    "ctrl_l": "Left Ctrl",
    "alt_r": "Right Alt",
    "alt_l": "Left Alt",
    "caps_lock": "Caps Lock",
    "f9": "F9",
    "f10": "F10",
    "scroll_lock": "Scroll Lock",
}

# Windows marks keystrokes made by software, not fingers, with this flag.
_LLKHF_INJECTED = 0x10


def friendly_name(key_name: str) -> str:
    """The name a person would use: "Right Ctrl", not "ctrl_r"."""
    return FRIENDLY.get(key_name, key_name)


def _real_keys_only(msg, data) -> bool:  # noqa: ANN001
    """Drop synthetic keystrokes before they reach the callbacks.

    Murmur itself sends Ctrl+V to paste the finished text. Without this
    filter, that synthetic Ctrl could be mistaken for the talk key and
    start a new recording.
    """
    return not (data.flags & _LLKHF_INJECTED)


class PushToTalk:
    """Calls on_press once when held, on_release once when let go."""

    def __init__(
        self,
        key_name: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        if key_name not in KEY_MAP:
            raise ValueError(
                f"Unknown hotkey {key_name!r}. Pick one of: {', '.join(KEY_MAP)}"
            )
        self._key = KEY_MAP[key_name]
        self._on_press = on_press
        self._on_release = on_release
        self._held = False
        self._listener: keyboard.Listener | None = None

    def _handle_press(self, key) -> None:  # noqa: ANN001
        if key == self._key and not self._held:
            self._held = True
            self._on_press()

    def _handle_release(self, key) -> None:  # noqa: ANN001
        if key == self._key and self._held:
            self._held = False
            self._on_release()

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._handle_press,
            on_release=self._handle_release,
            win32_event_filter=_real_keys_only,
        )
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
