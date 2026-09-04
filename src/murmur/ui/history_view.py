"""Past transcriptions. Searchable, copyable, and it shows what the
dictionary changed."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from . import theme
from .. import config, learn
from ..dictionary import Dictionary
from ..history import Entry, History
from ..hotkey import friendly_name
from .tokens import COLOUR as C, SPACE, SIZE, TYPE
from .widgets import SilkLabel


class _TranscriptTable(QTableWidget):
    """A table that explains itself while it is still empty."""

    empty_text = ""

    def paintEvent(self, event) -> None:  # noqa: ANN001, N802
        super().paintEvent(event)
        if self.rowCount() == 0 and self.empty_text:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(C.ink_faint))
            painter.setFont(theme.body_font())
            painter.drawText(
                self.viewport().rect(), Qt.AlignCenter, self.empty_text
            )


class HistoryView(QWidget):
    status = Signal(str)
    learned = Signal()

    COL_TIME, COL_TEXT, COL_FIXED, COL_COPY = range(4)

    def __init__(
        self,
        history: History,
        dictionary: Dictionary,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._history = history
        self._dictionary = dictionary
        self._rows: list[Entry] = []
        self._filling = False

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
        root.setSpacing(SPACE.md)

        bar = QHBoxLayout()
        bar.setSpacing(SPACE.sm)
        bar.addWidget(SilkLabel("Search"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("filter transcripts")
        self.search.textChanged.connect(self.refresh)
        bar.addWidget(self.search, 1)

        self.count = SilkLabel("")
        bar.addWidget(self.count)

        delete_button = QPushButton("Delete")
        delete_button.setObjectName("Tiny")
        delete_button.clicked.connect(self._delete_selected)
        bar.addWidget(delete_button)

        clear_button = QPushButton("Clear all")
        clear_button.setObjectName("Tiny")
        clear_button.clicked.connect(self._clear)
        bar.addWidget(clear_button)
        root.addLayout(bar)

        self.table = _TranscriptTable(0, 4)
        talk_key = friendly_name(config.load()["hotkey"]["key"])
        self.table.empty_text = (
            "Nothing here yet.\n\n"
            f"Hold {talk_key} in any app, say something, and let go.\n"
            "The words land where your cursor is, and a copy is kept here.\n\n"
            "Heard something wrong? Double-click the transcript and fix it —\n"
            "Murmur learns from your edit and stops making that mistake."
        )
        self.table.setHorizontalHeaderLabels(["TIME", "TRANSCRIPT", "FIXED", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        self.table.itemChanged.connect(self._edited)
        self.table.setWordWrap(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setFont(theme.silkscreen_font())
        header.setSectionResizeMode(self.COL_TIME, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_TEXT, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_FIXED, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_COPY, QHeaderView.Fixed)
        self.table.setColumnWidth(self.COL_TIME, 134)
        self.table.setColumnWidth(self.COL_FIXED, 220)
        self.table.setColumnWidth(self.COL_COPY, 78)
        self.table.verticalHeader().setDefaultSectionSize(SIZE.row_h + 2)
        root.addWidget(self.table, 1)

        self.detail = QLabel("")
        self.detail.setObjectName("Hint")
        self.detail.setWordWrap(True)
        self.detail.setMinimumHeight(34)
        self.table.itemSelectionChanged.connect(self._show_detail)
        root.addWidget(self.detail)

        self.refresh()

    # ---- data ----------------------------------------------------------

    def refresh(self) -> None:
        self._filling = True
        self._rows = self._history.search(self.search.text())
        self.table.setRowCount(0)
        for entry in self._rows:
            self._add_row(entry)
        self._filling = False
        total = len(self._history.entries)
        shown = len(self._rows)
        self.count.setText(
            f"{shown} of {total}" if shown != total else f"{total} kept"
        )

    def _add_row(self, entry: Entry) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        time_item = QTableWidgetItem(entry.when.strftime("%d %b  %H:%M"))
        time_item.setFont(theme.mono_font(TYPE.size_micro))
        time_item.setForeground(QColor(C.ink_dim))
        time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, self.COL_TIME, time_item)

        # The one editable cell: fix the words, Murmur learns from it.
        text_item = QTableWidgetItem(entry.final.replace("\n", " ¶ "))
        text_item.setToolTip(
            f"{entry.final}\n\nDouble-click to fix a word — Murmur learns from it."
        )
        self.table.setItem(row, self.COL_TEXT, text_item)

        if entry.was_corrected:
            summary = ", ".join(
                f"{c.heard} → {c.written}" for c in entry.corrections
            )
            fixed_item = QTableWidgetItem(summary)
            fixed_item.setToolTip(summary)
            fixed_item.setForeground(QColor(C.accent))
        else:
            fixed_item = QTableWidgetItem("—")
            fixed_item.setForeground(QColor(C.ink_faint))
        fixed_item.setFont(theme.mono_font(TYPE.size_micro))
        fixed_item.setFlags(fixed_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, self.COL_FIXED, fixed_item)

        copy_button = QPushButton("Copy")
        copy_button.setObjectName("Tiny")
        copy_button.clicked.connect(lambda _=False, e=entry: self._copy(e))
        self.table.setCellWidget(row, self.COL_COPY, copy_button)

    # ---- learning from edits --------------------------------------------

    def _edited(self, item: QTableWidgetItem) -> None:
        if self._filling or item.column() != self.COL_TEXT:
            return
        row = item.row()
        if not (0 <= row < len(self._rows)):
            return
        entry = self._rows[row]
        new_final = item.text().replace(" ¶ ", "\n").strip()
        if not new_final or new_final == entry.final:
            QTimer.singleShot(0, self.refresh)
            return

        old_final = entry.final
        self._history.update(entry.id, new_final)
        lesson = learn.teach(self._dictionary, old_final, new_final)

        if lesson.learned:
            fixes = ", ".join(f'"{h}" → "{w}"' for h, w in lesson.learned)
            self.status.emit(f"Saved. Learned: {fixes}")
            self.learned.emit()
        elif lesson.skipped:
            self.status.emit(
                "Saved. Nothing learned — the changed words are too "
                "ordinary to make a safe rule."
            )
        else:
            self.status.emit("Transcript updated")
        QTimer.singleShot(0, self.refresh)

    # ---- actions --------------------------------------------------------

    def _selected(self) -> Entry | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None

    def _copy(self, entry: Entry) -> None:
        QGuiApplication.clipboard().setText(entry.final)
        self.status.emit("Copied to clipboard")

    def _delete_selected(self) -> None:
        entry = self._selected()
        if entry:
            self._history.delete(entry.id)
            self.refresh()
            self.status.emit("Transcript deleted")

    def _clear(self) -> None:
        total = len(self._history.entries)
        if not total:
            return
        answer = QMessageBox.question(
            self,
            "Clear all transcripts",
            f"Delete all {total} transcripts? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        self._history.clear()
        self.refresh()
        self.status.emit("History cleared")

    def _show_detail(self) -> None:
        entry = self._selected()
        if not entry:
            self.detail.setText("")
            return
        parts = [f"{entry.seconds:.1f}s  ·  {entry.engine}"]
        if entry.was_corrected:
            for correction in entry.corrections:
                parts.append(
                    f'dictionary: "{correction.heard}" → '
                    f'"{correction.written}"  ×{correction.count}'
                )
            if entry.raw != entry.final:
                parts.append(f"before: {entry.raw}")
        else:
            parts.append("dictionary: nothing fired")
        self.detail.setText("     ".join(parts))
