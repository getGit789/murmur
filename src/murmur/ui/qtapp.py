"""Start the desktop app.

The window is the app now. The tray icon is secondary: it keeps the
push to talk hotkey alive while you are working somewhere else.
"""

from __future__ import annotations

import functools
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QImage, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .. import brand, config, logsetup
from ..dictionary import Dictionary
from ..history import History
from ..hotkey import PushToTalk
from . import theme
from .controller import Controller
from .main_window import MainWindow
from .pill import Pill


@functools.lru_cache(maxsize=None)
def _icon(state: str = "idle") -> QIcon:
    """The same mark at every size, so the tray, the taskbar and the
    title bar each get one drawn for them instead of a scaled copy."""
    icon = QIcon()
    for size in brand.ICO_SIZES:
        image = brand.draw_mark(size, state).convert("RGBA")
        qimage = QImage(
            image.tobytes("raw", "RGBA"), image.width, image.height,
            QImage.Format_RGBA8888,
        )
        icon.addPixmap(QPixmap.fromImage(qimage))
    return icon


class HotkeyBridge(QObject):
    """pynput fires on its own thread. Qt must be touched on the UI thread,
    so the press is bounced across as a signal."""

    pressed = Signal()
    released = Signal()



# One copy only. A second copy would hear the same hotkey and paste the
# same text again, so it hands over to the copy already running.
_SOCKET = "murmur-single-instance"


def _hand_over_to_running_copy(ask_to_show: bool) -> bool:
    """True when another Murmur answered. Then this copy should quit."""
    probe = QLocalSocket()
    probe.connectToServer(_SOCKET)
    if not probe.waitForConnected(500):
        return False
    if ask_to_show:
        probe.write(b"show")
        probe.flush()
        probe.waitForBytesWritten(500)
    probe.disconnectFromServer()
    return True


def _claim_single_instance(window: MainWindow) -> QLocalServer:
    """Answer later copies. A word from one of them opens the window."""
    QLocalServer.removeServer(_SOCKET)  # clear a socket left by a crash
    server = QLocalServer()
    server.listen(_SOCKET)

    def greet() -> None:
        connection = server.nextPendingConnection()
        if connection is None:
            return
        connection.setParent(server)  # keep it alive
        connection.readyRead.connect(lambda: _bring_to_front(window))
        connection.disconnected.connect(connection.deleteLater)

    server.newConnection.connect(greet)
    return server


def run() -> int:
    logsetup.start()
    settings = config.load()

    app = QApplication(sys.argv)
    app.setApplicationName(brand.NAME)
    app.setApplicationDisplayName(brand.NAME)
    app.setOrganizationName(brand.NAME)
    app.setWindowIcon(_icon("recording"))
    app.setStyleSheet(theme.qss())
    app.setQuitOnLastWindowClosed(False)

    hidden = _start_hidden(settings)
    if _hand_over_to_running_copy(ask_to_show=not hidden):
        print("[single] Murmur is already running. Nothing new started.")
        return 0

    history = History()
    dictionary = Dictionary.load()

    window = MainWindow(history, dictionary)
    controller = Controller(history, dictionary)
    pill = Pill()
    pill.set_level_source(lambda: controller.recorder.level)
    show_pill = bool(settings["feedback"].get("pill", True))

    # ---- wiring: controller -> views -----------------------------------

    # The pill belongs to a dictation cycle only. It must not appear
    # while the model is warming up at launch.
    cycle = {"active": False}

    def on_state(state: str, text: str) -> None:
        window.deck.set_state(state, text)
        window.set_recording(state == "recording")
        window.statusBar().showMessage(text)
        tray.setIcon(_icon(state))
        tray.setToolTip(f"{brand.NAME} — {text}")
        if state == "recording":
            cycle["active"] = True
        if show_pill and cycle["active"]:
            if state in ("recording", "working"):
                pill.show_state(state, "" if state == "recording" else "thinking")
            else:
                QTimer.singleShot(700, pill.hide_pill)
        if state in ("idle", "error"):
            cycle["active"] = False

    controller.state_changed.connect(on_state)
    controller.level_changed.connect(window.deck.set_level)
    controller.seconds_changed.connect(window.deck.set_seconds)
    controller.engine_ready.connect(window.deck.set_engine)
    controller.entry_added.connect(lambda _entry: window.history_view.refresh())

    window.start_requested.connect(controller.start)
    window.stop_requested.connect(controller.stop)
    window.dictionary_changed.connect(controller.reload_dictionary)
    window.fast_mode_changed.connect(controller.reload_engine)

    # ---- tray: secondary, for when the window is not in front -----------

    tray = QSystemTrayIcon(_icon("idle"))
    tray.setToolTip(f"{brand.NAME} — {brand.TAGLINE}")
    menu = QMenu()

    open_action = QAction(f"Open {brand.NAME}")
    open_action.triggered.connect(lambda: _bring_to_front(window))
    menu.addAction(open_action)

    talk_action = QAction("Start / stop recording")
    talk_action.triggered.connect(controller.toggle)
    menu.addAction(talk_action)

    menu.addSeparator()
    settings_action = QAction("Settings...")
    settings_action.triggered.connect(window.open_settings)
    menu.addAction(settings_action)

    menu.addSeparator()
    quit_action = QAction("Quit")
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: _bring_to_front(window)
        if reason == QSystemTrayIcon.DoubleClick
        else None
    )
    tray.show()

    # ---- the global hotkey, alive whatever has focus --------------------

    bridge = HotkeyBridge()
    bridge.pressed.connect(controller.start)
    bridge.released.connect(controller.stop)
    hotkey = PushToTalk(
        settings["hotkey"]["key"],
        on_press=bridge.pressed.emit,
        on_release=bridge.released.emit,
    )
    hotkey.start()

    # ---- shutdown -------------------------------------------------------

    def quit_app() -> None:
        server.close()
        hotkey.stop()
        controller.shutdown()
        pill.hide_pill()
        tray.hide()
        app.quit()

    quit_action.triggered.connect(quit_app)
    window.quit_requested.connect(quit_app)

    # Tray only when asked. The hotkey is already listening, so you can
    # dictate without the window ever being on screen.
    server = _claim_single_instance(window)
    if not hidden:
        window.show()
        _maybe_offer_fast_mode(window, settings)
    controller.warm_up()
    return app.exec()


def _maybe_offer_fast_mode(window: MainWindow, settings) -> None:
    """First time only, if there is no key, show the one-click setup.

    A marker file makes sure this happens once, never on every launch.
    """
    from ..engines.groq_api import read_key

    marker = config.config_dir() / ".fastmode_offered"
    if marker.exists() or read_key():
        return
    if settings.get("engine", {}).get("backend") == "groq":
        return
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("offered", encoding="utf-8")
    except OSError:
        pass
    QTimer.singleShot(700, window.open_groq_setup)


def _start_hidden(settings) -> bool:
    """True when Murmur should come up in the tray with no window.

    Either the --hidden flag (the Windows startup shortcut uses it) or
    `[startup] hidden = true` in config.toml.
    """
    if "--hidden" in sys.argv:
        return True
    return bool(settings.get("startup", {}).get("hidden", False))


def _bring_to_front(window: MainWindow) -> None:
    window.show()
    window.setWindowState(
        window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
    )
    window.raise_()
    window.activateWindow()
