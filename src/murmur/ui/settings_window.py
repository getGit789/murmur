"""Settings. Ctrl+comma. Holds the hotkey and the model."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from .. import autostart, config
from ..engines.groq_api import key_path
from . import theme
from ..hotkey import KEY_MAP, friendly_name
from .tokens import SIZE, SPACE, TYPE
from .widgets import Panel, SilkLabel

MODELS = ["tiny.en", "base.en", "small.en", "medium.en"]
BACKENDS = ["local", "groq"]
CLEANUP = ["none", "rules", "llm"]


class SettingsWindow(QDialog):
    saved = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(*SIZE.settings_size)
        self.settings = config.load()

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
        root.setSpacing(SPACE.md)

        panel = Panel()
        form = QFormLayout(panel)
        form.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
        form.setSpacing(SPACE.md)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.hotkey = QComboBox()
        for key in sorted(KEY_MAP):
            self.hotkey.addItem(friendly_name(key), key)
        current = self.hotkey.findData(self.settings["hotkey"]["key"])
        self.hotkey.setCurrentIndex(max(0, current))
        form.addRow(SilkLabel("Hold to talk"), self.hotkey)

        self.backend = QComboBox()
        self.backend.addItems(BACKENDS)
        self.backend.setCurrentText(self.settings["engine"]["backend"])
        form.addRow(SilkLabel("Engine"), self.backend)

        self.model = QComboBox()
        self.model.addItems(MODELS)
        self.model.setCurrentText(self.settings["engine"]["local"]["model"])
        form.addRow(SilkLabel("Model"), self.model)

        self.cleanup = QComboBox()
        self.cleanup.addItems(CLEANUP)
        self.cleanup.setCurrentText(self.settings["cleanup"]["mode"])
        form.addRow(SilkLabel("Cleanup"), self.cleanup)

        self.groq_key = QLineEdit()
        try:
            self.groq_key.setText(key_path().read_text(encoding="utf-8").strip())
        except OSError:
            pass
        if not self.groq_key.text() and os.environ.get("GROQ_API_KEY", "").strip():
            self.groq_key.setPlaceholderText("using the GROQ_API_KEY variable")
        else:
            self.groq_key.setPlaceholderText("gsk_...  (free key at console.groq.com)")
        form.addRow(SilkLabel("Groq key"), self.groq_key)

        self.pill = QCheckBox("Show the floating bar while recording")
        self.pill.setChecked(bool(self.settings["feedback"].get("pill", True)))
        form.addRow(SilkLabel("Overlay"), self.pill)

        self.beep = QCheckBox("Beep on start and stop")
        self.beep.setChecked(bool(self.settings["feedback"].get("beep", True)))
        form.addRow(SilkLabel("Sound"), self.beep)

        self.autostart_box = QCheckBox("Start Murmur when Windows starts")
        self.autostart_box.setChecked(autostart.is_enabled())
        form.addRow(SilkLabel("Startup"), self.autostart_box)

        self.hidden_box = QCheckBox("Open in the tray, with no window")
        self.hidden_box.setChecked(
            bool(self.settings.get("startup", {}).get("hidden", False))
        )
        form.addRow(SilkLabel("Window"), self.hidden_box)

        root.addWidget(panel)

        note = QLabel(
            "The talk key works everywhere, even with this window closed. "
            "Changing the engine or model takes effect the next time "
            "Murmur starts. The Windows startup copy always opens in "
            "the tray."
        )
        note.setObjectName("Hint")
        note.setWordWrap(True)
        root.addWidget(note)

        path = QLabel(str(config.config_path()))
        path.setObjectName("Hint")
        path.setFont(theme.mono_font(TYPE.size_micro))
        root.addWidget(path)
        root.addStretch(1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton("Save")
        save.setDefault(True)
        save.clicked.connect(self._save)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def _save(self) -> None:
        text = _read_config_text()
        text = _set(text, "hotkey", "key", f'"{self.hotkey.currentData()}"')
        text = _set(text, "engine", "backend", f'"{self.backend.currentText()}"')
        text = _set(text, "engine.local", "model", f'"{self.model.currentText()}"')
        text = _set(text, "cleanup", "mode", f'"{self.cleanup.currentText()}"')
        text = _set(text, "feedback", "pill", "true" if self.pill.isChecked() else "false")
        text = _set(text, "feedback", "beep", "true" if self.beep.isChecked() else "false")
        text = _set(text, "startup", "hidden", "true" if self.hidden_box.isChecked() else "false")

        path = config.config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

        # The Groq key lives in its own file, out of the shareable config.
        key = self.groq_key.text().strip()
        key_file = key_path()
        if key:
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_text(key, encoding="utf-8")
        elif key_file.exists():
            key_file.unlink()

        want_autostart = self.autostart_box.isChecked()
        if want_autostart != autostart.is_enabled():
            try:
                autostart.enable() if want_autostart else autostart.disable()
            except Exception as error:
                print(f"[settings] autostart failed: {error}")

        self.saved.emit()
        self.accept()


def _read_config_text() -> str:
    path = config.config_path()
    if path.exists():
        return path.read_text(encoding="utf-8")
    example = Path(__file__).resolve().parents[3] / "config.example.toml"
    if example.exists():
        return example.read_text(encoding="utf-8")
    return ""


def _set(text: str, section: str, key: str, value: str) -> str:
    """Replace one key inside one section, leaving comments alone."""
    lines = text.splitlines()
    current = ""
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped[1:-1]
            continue
        if current == section and stripped.split("=")[0].strip() == key:
            lines[index] = f"{key} = {value}"
            return "\n".join(lines) + "\n"

    # section or key missing: append it
    if f"[{section}]" not in text:
        lines += ["", f"[{section}]", f"{key} = {value}"]
    else:
        for index, line in enumerate(lines):
            if line.strip() == f"[{section}]":
                lines.insert(index + 1, f"{key} = {value}")
                break
    return "\n".join(lines) + "\n"
