"""The deck: the silver top strip with the glass display on it.

The display carries everything that moves — the record lamp, the
status text, the elapsed counter and the level meter — so your eye
only ever has to watch one window.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from . import theme
from .tokens import SPACE, TYPE
from .widgets import DisplayGlass, MetalPlate, Panel, RecordLamp, SegmentMeter, SilkLabel


class Deck(QWidget):
    """Looks like the front of the machine."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        plate = MetalPlate(30)
        plate_layout = QHBoxLayout(plate)
        plate_layout.setContentsMargins(SPACE.lg, 0, SPACE.lg, 0)
        title = SilkLabel("Murmur  ·  Dictation", on_metal=True, size=10)
        plate_layout.addWidget(title)
        plate_layout.addStretch(1)
        self.engine_label = SilkLabel("", on_metal=True, size=9)
        plate_layout.addWidget(self.engine_label)
        root.addWidget(plate)

        body = Panel()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(SPACE.lg, SPACE.md, SPACE.lg, SPACE.md)

        glass = DisplayGlass()
        glass_layout = QVBoxLayout(glass)
        glass_layout.setContentsMargins(SPACE.lg, SPACE.md, SPACE.lg, SPACE.md)
        glass_layout.setSpacing(SPACE.sm)

        status_row = QHBoxLayout()
        status_row.setSpacing(SPACE.sm)
        self.lamp = RecordLamp()
        status_row.addWidget(self.lamp)
        self.state_label = QLabel("IDLE")
        self.state_label.setObjectName("LCDText")
        self.state_label.setFont(theme.mono_font(TYPE.size_body))
        status_row.addWidget(self.state_label, 1)
        self.counter = QLabel("0:00.0")
        self.counter.setObjectName("LCDBig")
        self.counter.setFont(theme.mono_font(TYPE.size_counter))
        self.counter.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_row.addWidget(self.counter)
        glass_layout.addLayout(status_row)

        self.meter = SegmentMeter()
        glass_layout.addWidget(self.meter)

        body_layout.addWidget(glass)
        root.addWidget(body)

    # ---- driven by the controller ---------------------------------------

    def set_level(self, level: float) -> None:
        self.meter.set_level(level)

    def set_state(self, state: str, text: str) -> None:
        self.lamp.set_lit(state == "recording")
        self.state_label.setText(text.upper())

    def set_seconds(self, seconds: float) -> None:
        minutes = int(seconds) // 60
        rest = seconds - minutes * 60
        self.counter.setText(f"{minutes}:{rest:04.1f}")

    def set_engine(self, text: str) -> None:
        self.engine_label.setText(text)
