"""The main window: menu bar, transport deck, and the three panels."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QStatusBar,
    QTabWidget, QVBoxLayout, QWidget,
)

from .. import brand, config, logsetup
from ..dictionary import Dictionary, dictionary_path
from ..history import History
from ..hotkey import friendly_name
from .deck import Deck
from .dictionary_view import DictionaryView
from .history_view import HistoryView
from .settings_window import SettingsWindow
from .tokens import SIZE, SPACE
from .widgets import Seam


class MainWindow(QMainWindow):
    start_requested = Signal()
    stop_requested = Signal()
    quit_requested = Signal()
    dictionary_changed = Signal()

    def __init__(self, history: History, dictionary: Dictionary) -> None:
        super().__init__()
        self.setWindowTitle(brand.NAME)
        self.setMinimumSize(*SIZE.window_min)
        self.resize(*SIZE.window_default)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.deck = Deck()
        layout.addWidget(self.deck)
        layout.addWidget(Seam())

        talk_key = friendly_name(config.load()["hotkey"]["key"])

        # transport keys sit under the deck, on the chassis
        transport = QWidget()
        transport_layout = QHBoxLayout(transport)
        transport_layout.setContentsMargins(SPACE.lg, SPACE.md, SPACE.lg, SPACE.md)
        transport_layout.setSpacing(SPACE.md)

        self.start_button = QPushButton("Record")
        self.start_button.setObjectName("Transport")
        self.start_button.setToolTip(f"Or just hold {talk_key}, in any app")
        self.start_button.clicked.connect(self.start_requested.emit)
        transport_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("Transport")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        transport_layout.addWidget(self.stop_button)

        hint = QLabel(
            f"Hold {talk_key} in any app, talk, let go — "
            f"the words are typed where your cursor is."
        )
        hint.setObjectName("Hint")
        transport_layout.addWidget(hint)
        transport_layout.addStretch(1)
        layout.addWidget(transport)
        layout.addWidget(Seam())

        self.tabs = QTabWidget()
        self.history_view = HistoryView(history, dictionary)
        self.dictionary_view = DictionaryView(dictionary)
        self.tabs.addTab(self.history_view, "TRANSCRIPTS")
        self.tabs.addTab(self.dictionary_view, "DICTIONARY")
        layout.addWidget(self.tabs, 1)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(brand.TAGLINE)

        self.history_view.status.connect(self.statusBar().showMessage)
        self.dictionary_view.status.connect(self.statusBar().showMessage)
        self.dictionary_view.changed.connect(self.dictionary_changed.emit)

        # A fixed transcript teaches the dictionary; every reader follows.
        self.history_view.learned.connect(self.dictionary_view.refresh)
        self.history_view.learned.connect(self.dictionary_changed.emit)

        self._build_menus()

    # ---- menus ----------------------------------------------------------

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()
        for label, path_fn in [
            ("Open settings file", config.config_path),
            ("Open dictionary file", dictionary_path),
            ("Open log file", logsetup.log_path),
        ]:
            action = QAction(label, self)
            action.triggered.connect(lambda _=False, fn=path_fn: _reveal(fn()))
            file_menu.addAction(action)

        file_menu.addSeparator()
        hide_action = QAction("&Hide to tray", self)
        hide_action.setShortcut(QKeySequence("Ctrl+W"))
        hide_action.triggered.connect(self.hide)
        file_menu.addAction(hide_action)

        quit_action = QAction("&Quit Murmur", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.quit_requested.emit)
        file_menu.addAction(quit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        find_action = QAction("&Find transcript", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self._focus_search)
        edit_menu.addAction(find_action)

        view_menu = self.menuBar().addMenu("&View")
        for index, (label, shortcut) in enumerate(
            [("&Transcripts", "Ctrl+1"), ("&Dictionary", "Ctrl+2")]
        ):
            action = QAction(label, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(lambda _=False, i=index: self.tabs.setCurrentIndex(i))
            view_menu.addAction(action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About Murmur", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _focus_search(self) -> None:
        if self.tabs.currentIndex() == 0:
            self.history_view.search.setFocus()
            self.history_view.search.selectAll()
        else:
            self.dictionary_view.search.setFocus()
            self.dictionary_view.search.selectAll()

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About Murmur",
            f"<b>{brand.NAME}</b><br>{brand.TAGLINE}<br><br>"
            f"Push to talk dictation.<br>"
            f"Speech stays on this machine when the engine is set to local.",
        )

    def open_settings(self) -> None:
        window = SettingsWindow(self)
        window.saved.connect(
            lambda: self.statusBar().showMessage(
                "Settings saved. Restart Murmur to change engine or model."
            )
        )
        window.exec()

    # ---- driven by the controller ---------------------------------------

    def set_recording(self, recording: bool) -> None:
        self.start_button.setEnabled(not recording)
        self.stop_button.setEnabled(recording)

    def closeEvent(self, event) -> None:  # noqa: ANN001, N802
        """Closing the window leaves it running in the tray."""
        event.ignore()
        self.hide()
        self.statusBar().showMessage("Still running in the tray")


def _reveal(path) -> None:  # noqa: ANN001
    import os
    import subprocess

    try:
        os.startfile(str(path))  # noqa: S606
    except Exception:
        subprocess.run(["notepad", str(path)], check=False)
