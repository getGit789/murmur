"""The floating pill: small, dark, quiet.

Shows up while you hold the talk key, never takes focus. The bars
follow your voice while you speak; while you are silent they keep a
gentle flow, never a flat line. While Murmur transcribes, one soft
teal wave sweeps across. No dots, no text.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPropertyAnimation, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from .tokens import COLOUR as C, MOTION

WIDTH, HEIGHT = 132, 30
BOTTOM_GAP = 72
BARS = 24
PAD = 12
FPS = 30


class Pill(QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool                       # keeps it out of the taskbar
            | Qt.WindowTransparentForInput  # clicks pass straight through
            | Qt.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(WIDTH, HEIGHT)

        self._levels = [0.0] * BARS
        self._state = "idle"
        self._phase = 0
        self._level_source = lambda: 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(MOTION.fade_ms)
        self._fade.finished.connect(self._after_fade)
        self._place()

    def set_level_source(self, source) -> None:  # noqa: ANN001
        self._level_source = source

    def _place(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.move(
            area.center().x() - WIDTH // 2,
            area.bottom() - BOTTOM_GAP - HEIGHT,
        )

    # ---- lifecycle -------------------------------------------------------

    def show_state(self, state: str, label: str = "") -> None:
        # `label` is accepted so callers stay unchanged; the pill shows
        # no text any more.
        if state == "recording" and self._state != "recording":
            self._levels = [0.0] * BARS
        self._state = state
        self._place()
        if self.isHidden():
            self.setWindowOpacity(0.0)
            self.show()
        self._fade_to(1.0)
        if not self._timer.isActive():
            self._timer.start(int(1000 / FPS))

    def hide_pill(self) -> None:
        if self.isHidden():
            return
        self._fade_to(0.0)

    def _fade_to(self, end: float) -> None:
        self._fade.stop()
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(end)
        self._fade.start()

    def _after_fade(self) -> None:
        if self._fade.endValue() == 0.0:
            self._timer.stop()
            self.hide()

    # ---- animation -------------------------------------------------------

    def _tick(self) -> None:
        self._phase += 1
        if self._state == "recording":
            self._levels.pop(0)
            self._levels.append(max(0.0, min(1.0, self._level_source())))
        self.update()

    def _idle_half(self, index: int) -> float:
        """The resting flow: a slow ripple that never lies flat."""
        slow = math.sin(self._phase * 0.16 + index * 0.55)
        drift = math.sin(self._phase * 0.07 - index * 0.35)
        return 2.0 + 0.7 * slow + 0.5 * drift

    def _sweep_half(self, index: int) -> float:
        """Transcribing: one soft hump travelling along the bars."""
        span = BARS + 10
        head = (self._phase * 0.45) % span - 5
        bump = 4.2 * math.exp(-((index - head) ** 2) / 7.0)
        return self._idle_half(index) + bump

    # ---- painting --------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: ANN001, N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        radius = HEIGHT / 2

        body = QColor(C.lcd_bg)
        body.setAlpha(244)
        painter.setBrush(body)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), radius, radius)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 26), 1))
        painter.drawRoundedRect(
            QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), radius, radius
        )

        bar_colour = {
            "recording": C.pill_bar,
            "working": C.lcd_text,
            "error": C.record_glow,
        }.get(self._state, C.lcd_text_dim)

        slot = (WIDTH - 2 * PAD) / BARS
        bar_w = slot * 0.52
        centre = HEIGHT / 2
        max_half = centre - 5.0

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(bar_colour))
        for index in range(BARS):
            if self._state == "recording":
                voice = (self._levels[index] ** 0.8) * max_half
                half = max(self._idle_half(index), voice)
            elif self._state == "working":
                half = self._sweep_half(index)
            else:
                half = self._idle_half(index)
            half = max(1.0, min(max_half, half))
            x = PAD + index * slot + (slot - bar_w) / 2
            painter.drawRoundedRect(
                QRectF(x, centre - half, bar_w, half * 2), bar_w / 2, bar_w / 2
            )
