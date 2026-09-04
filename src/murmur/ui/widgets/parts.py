"""Plain surfaces and labels. All styling comes from theme.qss()."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .. import theme
from ..tokens import SPACE


class Panel(QFrame):
    """A working surface with a seam around it."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Panel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class Well(QFrame):
    """A recessed area. Lists and meters sit in these."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Well")


class Seam(QFrame):
    """A one pixel dark line between panels."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Seam")
        self.setFixedHeight(1)


class SilkLabel(QLabel):
    """A printed label: small, uppercase, tightly tracked."""

    def __init__(
        self,
        text: str = "",
        on_metal: bool = False,
        size: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.setObjectName("SilkOnMetal" if on_metal else "Silk")
        self.setFont(theme.silkscreen_font(size))


def titled(title: str, widget: QWidget, gap: int = SPACE.sm) -> QWidget:
    """A silkscreen title above a control."""
    holder = QWidget()
    layout = QVBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(gap)
    label = SilkLabel(title)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(label)
    layout.addWidget(widget)
    return holder
