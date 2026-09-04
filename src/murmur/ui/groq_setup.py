"""Turn on Fast Mode. A three-step wizard for the free Groq key.

Made to be obvious: get a key on the Groq site, paste it, save. When
it saves, it also switches the engine to Groq and asks the app to
reload, so the speed is on right away with no restart.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from .. import config
from ..engines.groq_api import key_path, read_key
from .tokens import SPACE, TYPE
from .widgets import Panel, SilkLabel

GROQ_KEYS_URL = "https://console.groq.com/keys"


class GroqSetupDialog(QDialog):
    """Get a free key, paste it, done."""

    applied = Signal()   # a key was saved; the engine should reload

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Turn on Fast Mode")
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
        root.setSpacing(SPACE.md)

        title = QLabel("Make Murmur type faster — for free.")
        title.setFont(theme_heading())
        title.setWordWrap(True)
        root.addWidget(title)

        blurb = QLabel(
            "Fast Mode uses Groq, a free cloud service, to turn your "
            "speech into text in about a second. Your voice is sent only "
            "to Groq to be transcribed. Three small steps:"
        )
        blurb.setObjectName("Hint")
        blurb.setWordWrap(True)
        root.addWidget(blurb)

        panel = Panel()
        steps = QVBoxLayout(panel)
        steps.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
        steps.setSpacing(SPACE.md)

        # Step 1: get the key
        steps.addWidget(SilkLabel("Step 1  ·  Get your free key"))
        one = QLabel(
            "Click the button. Your web browser opens the Groq key page. "
            "Sign in (Google works), then press <b>Create API Key</b>, give "
            "it any name, and press <b>Copy</b>."
        )
        one.setObjectName("Hint")
        one.setWordWrap(True)
        steps.addWidget(one)
        get_button = QPushButton("Open the Groq key page")
        get_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GROQ_KEYS_URL)))
        steps.addWidget(get_button)

        # Step 2 + 3: paste and save
        steps.addWidget(SilkLabel("Step 2  ·  Paste the key here"))
        row = QHBoxLayout()
        row.setSpacing(SPACE.sm)
        self.field = QLineEdit()
        self.field.setPlaceholderText("gsk_…")
        self.field.setText(read_key())
        self.field.textChanged.connect(self._revalidate)
        row.addWidget(self.field, 1)
        paste_button = QPushButton("Paste")
        paste_button.setObjectName("Tiny")
        paste_button.clicked.connect(self._paste)
        row.addWidget(paste_button)
        steps.addLayout(row)

        root.addWidget(panel)

        self.note = QLabel("")
        self.note.setObjectName("Hint")
        self.note.setWordWrap(True)
        root.addWidget(self.note)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        later = QPushButton("Later")
        later.clicked.connect(self.reject)
        buttons.addWidget(later)
        self.save_button = QPushButton("Save and turn on Fast Mode")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self._save)
        buttons.addWidget(self.save_button)
        root.addLayout(buttons)

        self._revalidate()

    # ---- helpers --------------------------------------------------------

    def _paste(self) -> None:
        text = QGuiApplication.clipboard().text().strip()
        if text:
            self.field.setText(text)

    def _revalidate(self) -> None:
        key = self.field.text().strip()
        if not key:
            self.note.setText("Paste your key above, then press Save.")
            self.save_button.setEnabled(False)
        elif not key.startswith("gsk_") or len(key) < 20:
            self.note.setText(
                "That does not look like a Groq key. It should start with "
                '"gsk_". Copy it again from the Groq page.'
            )
            self.save_button.setEnabled(True)
        else:
            self.note.setText("Looks good. Press Save to turn on Fast Mode.")
            self.save_button.setEnabled(True)

    def _save(self) -> None:
        key = self.field.text().strip()
        if not key:
            return
        path = key_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(key, encoding="utf-8")
        # Switch the engine over so the speed is on immediately.
        config.update_values([("engine", "backend", '"groq"')])
        self.applied.emit()
        self.note.setText("Fast Mode is on. ✓")
        self.accept()


def theme_heading():
    from . import theme

    return theme.body_font(TYPE.size_heading, bold=True)
