"""Instruments, painted by hand.

The silver plate, the record lamp, the dark display glass and the
segment level meter that lives on it. All of them read their colours
and sizes from tokens.py.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QWidget

from .. import theme
from ..tokens import BORDER, COLOUR as C, MOTION, RADIUS, SIZE


class MetalPlate(QWidget):
    """A brushed aluminium strip. Used for headers and the transport deck."""

    def __init__(self, height: int = 34, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(height)

    def paintEvent(self, event) -> None:  # noqa: ANN001, N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        rect = self.rect()
        painter.fillRect(rect, theme.plate_gradient())

        # brushed texture: faint horizontal grain
        pen = QPen(QColor(0, 0, 0, 10))
        painter.setPen(pen)
        for y in range(0, rect.height(), 3):
            painter.drawLine(0, y, rect.width(), y)

        # lit top lip, dark bottom seam
        painter.setPen(QPen(QColor(C.alu_edge), 1))
        painter.drawLine(0, 0, rect.width(), 0)
        painter.setPen(QPen(QColor(C.seam), 1))
        painter.drawLine(0, rect.height() - 1, rect.width(), rect.height() - 1)


class RecordLamp(QWidget):
    """The one red thing in the app. Rests on the display glass."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(SIZE.lamp + 6, SIZE.lamp + 6)
        self._lit = False

    def set_lit(self, lit: bool) -> None:
        if lit != self._lit:
            self._lit = lit
            self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001, N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        box = QRectF(3, 3, SIZE.lamp, SIZE.lamp)

        if self._lit:
            halo = QColor(C.record_glow)
            halo.setAlpha(60)
            painter.setBrush(halo)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(box.adjusted(-3, -3, 3, 3))

        painter.setBrush(QColor(C.record_glow if self._lit else C.record_dead))
        painter.setPen(QPen(QColor(C.lamp_ring), 1))
        painter.drawEllipse(box)


class DisplayGlass(QFrame):
    """The dark glass window on the front of the deck.

    Paints the glass; the lamp, status text, counter and meter sit on
    top of it as ordinary child widgets.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(SIZE.display_h)

    def paintEvent(self, event) -> None:  # noqa: ANN001, N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        painter.setBrush(QColor(C.lcd_bg))
        painter.setPen(QPen(QColor(C.lcd_frame), BORDER.hairline))
        painter.drawRoundedRect(rect, RADIUS.soft, RADIUS.soft)

        # the glass sits behind the panel face: a soft shadow at the top
        painter.setPen(QPen(QColor(0, 0, 0, 90), 1))
        painter.drawLine(
            int(rect.left()) + RADIUS.soft, int(rect.top()) + 1,
            int(rect.right()) - RADIUS.soft, int(rect.top()) + 1,
        )

        # faint scanlines, the VFD grain
        painter.setPen(QPen(QColor(255, 255, 255, 5)))
        for y in range(int(rect.top()) + 4, int(rect.bottom()) - 3, 3):
            painter.drawLine(int(rect.left()) + 3, y, int(rect.right()) - 3, y)


class SegmentMeter(QWidget):
    """A horizontal row of level segments: green, amber, then red.

    The lit bar follows the voice at once. The peak marker hangs back
    and falls slowly, like the hold LED on a deck.
    """

    SEGMENTS = 36
    GREEN_UNTIL = 0.60
    AMBER_UNTIL = 0.85

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(14)
        self._level = 0.0
        self._peak = 0.0

    def set_level(self, level: float) -> None:
        self._level = max(0.0, min(1.0, level))
        self._peak = max(self._peak * MOTION.meter_peak_decay, self._level)
        self.update()

    def _segment_colour(self, index: int) -> str:
        fraction = index / (self.SEGMENTS - 1)
        if fraction < self.GREEN_UNTIL:
            return C.level_green
        if fraction < self.AMBER_UNTIL:
            return C.level_amber
        return C.level_peak

    def paintEvent(self, event) -> None:  # noqa: ANN001, N802
        painter = QPainter(self)
        rect = self.rect()

        lit_count = int(self._level * self.SEGMENTS + 0.5)
        peak_index = int(self._peak * self.SEGMENTS + 0.5) - 1
        gap = 2
        width = (rect.width() - gap * (self.SEGMENTS - 1)) / self.SEGMENTS

        for index in range(self.SEGMENTS):
            x = index * (width + gap)
            lit = index < lit_count or index == peak_index
            colour = self._segment_colour(index) if lit else C.lcd_unlit
            painter.fillRect(
                QRectF(x, 0, width, rect.height()), QColor(colour)
            )
