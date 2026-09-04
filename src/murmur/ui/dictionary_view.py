"""Teach it your words.

Left: terms handed to the engine before it listens.
Right: correction pairs applied after it listens.
Both write the same plain file, so you can edit it by hand too.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from . import theme
from ..dictionary import MAX_BIAS_TERMS, Dictionary, check_risk, dictionary_path
from .tokens import SPACE, SIZE, TYPE
from .widgets import Panel, SilkLabel


class DictionaryView(QWidget):
    status = Signal(str)
    changed = Signal()

    def __init__(self, dictionary: Dictionary, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dictionary = dictionary

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
        root.setSpacing(SPACE.md)

        search_bar = QHBoxLayout()
        search_bar.setSpacing(SPACE.sm)
        search_bar.addWidget(SilkLabel("Search"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("filter both lists")
        self.search.textChanged.connect(self.refresh)
        search_bar.addWidget(self.search, 1)
        file_hint = QLabel(str(dictionary_path()))
        file_hint.setObjectName("Hint")
        file_hint.setFont(theme.mono_font(TYPE.size_micro))
        search_bar.addWidget(file_hint)
        root.addLayout(search_bar)

        columns = QHBoxLayout()
        columns.setSpacing(SPACE.lg)
        columns.addWidget(self._build_terms(), 1)
        columns.addWidget(self._build_corrections(), 2)
        root.addLayout(columns, 1)

        self.warning = QLabel("")
        self.warning.setObjectName("Warning")
        self.warning.setWordWrap(True)
        self.warning.setMinimumHeight(32)
        root.addWidget(self.warning)

        self.refresh()

    # ---- terms ----------------------------------------------------------

    def _build_terms(self) -> QWidget:
        panel = Panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(SPACE.md, SPACE.md, SPACE.md, SPACE.md)
        layout.setSpacing(SPACE.sm)

        layout.addWidget(SilkLabel("Words to lean toward"))
        hint = QLabel(
            f"Handed to the engine before it listens. "
            f"Only the first {MAX_BIAS_TERMS} are sent — a long list makes it drift."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.terms_list = QListWidget()
        self.terms_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.terms_list, 1)

        row = QHBoxLayout()
        row.setSpacing(SPACE.sm)
        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("Anthropic")
        self.term_input.returnPressed.connect(self._add_term)
        row.addWidget(self.term_input, 1)
        add = QPushButton("Add")
        add.setObjectName("Tiny")
        add.clicked.connect(self._add_term)
        row.addWidget(add)
        remove = QPushButton("Remove")
        remove.setObjectName("Tiny")
        remove.clicked.connect(self._remove_term)
        row.addWidget(remove)
        layout.addLayout(row)
        return panel

    def _add_term(self) -> None:
        term = self.term_input.text().strip()
        if not term:
            return
        self._dictionary.add_term(term)
        self.term_input.clear()
        self.refresh()
        self.changed.emit()
        self.status.emit(f'Added "{term}"')

    def _remove_term(self) -> None:
        item = self.terms_list.currentItem()
        if not item:
            return
        self._dictionary.remove_term(item.text())
        self.refresh()
        self.changed.emit()
        self.status.emit("Term removed")

    # ---- corrections ----------------------------------------------------

    def _build_corrections(self) -> QWidget:
        panel = Panel()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(SPACE.md, SPACE.md, SPACE.md, SPACE.md)
        layout.setSpacing(SPACE.sm)

        layout.addWidget(SilkLabel("When you hear ... write ..."))
        hint = QLabel(
            "Applied after listening. Whole words, any case. Also catches "
            "glued and hyphenated forms, so one rule covers "
            "“cloud code”, “Cloud-Code” and “CloudCode”."
        )
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.corrections_table = QTableWidget(0, 2)
        self.corrections_table.setHorizontalHeaderLabels(["HEARD", "WRITTEN"])
        self.corrections_table.verticalHeader().setVisible(False)
        self.corrections_table.setAlternatingRowColors(True)
        self.corrections_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.corrections_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.corrections_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.corrections_table.setShowGrid(False)
        header = self.corrections_table.horizontalHeader()
        header.setFont(theme.silkscreen_font())
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.corrections_table.verticalHeader().setDefaultSectionSize(SIZE.row_h)
        self.corrections_table.itemSelectionChanged.connect(self._load_selected)
        layout.addWidget(self.corrections_table, 1)

        row = QHBoxLayout()
        row.setSpacing(SPACE.sm)
        self.heard_input = QLineEdit()
        self.heard_input.setPlaceholderText("cloud code")
        self.heard_input.textChanged.connect(self._preview_risk)
        row.addWidget(self.heard_input, 1)
        arrow = QLabel("→")
        arrow.setObjectName("Hint")
        row.addWidget(arrow)
        self.written_input = QLineEdit()
        self.written_input.setPlaceholderText("Claude Code")
        self.written_input.textChanged.connect(self._preview_risk)
        self.written_input.returnPressed.connect(self._save_correction)
        row.addWidget(self.written_input, 1)
        layout.addLayout(row)

        buttons = QHBoxLayout()
        buttons.setSpacing(SPACE.sm)
        buttons.addStretch(1)
        save = QPushButton("Save")
        save.setObjectName("Tiny")
        save.clicked.connect(self._save_correction)
        buttons.addWidget(save)
        delete = QPushButton("Delete")
        delete.setObjectName("Tiny")
        delete.clicked.connect(self._delete_correction)
        buttons.addWidget(delete)
        layout.addLayout(buttons)
        return panel

    def _selected_heard(self) -> str:
        row = self.corrections_table.currentRow()
        item = self.corrections_table.item(row, 0) if row >= 0 else None
        return item.text() if item else ""

    def _load_selected(self) -> None:
        heard = self._selected_heard()
        if heard:
            self.heard_input.setText(heard)
            self.written_input.setText(self._dictionary.corrections.get(heard, ""))

    def _preview_risk(self) -> None:
        heard = self.heard_input.text().strip()
        written = self.written_input.text().strip()
        if not heard and not written:
            self.warning.setText("")
            return
        risk = check_risk(heard, written)
        self.warning.setText(f"⚠  {risk.message}" if risk else "")

    def _save_correction(self) -> None:
        heard = self.heard_input.text().strip()
        written = self.written_input.text().strip()
        risk = check_risk(heard, written)

        if risk and risk.level == "block":
            self.warning.setText(f"⚠  {risk.message}")
            return
        if risk and risk.level == "warn":
            answer = QMessageBox.warning(
                self,
                "Check this entry",
                f"{risk.message}\n\nAdd it anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        replacing = self._selected_heard()
        self._dictionary.set_correction(heard, written, replacing=replacing)
        self.heard_input.clear()
        self.written_input.clear()
        self.warning.setText("")
        self.refresh()
        self.changed.emit()
        self.status.emit(f'Saved "{heard}" → "{written}"')

    def _delete_correction(self) -> None:
        heard = self._selected_heard()
        if not heard:
            return
        self._dictionary.remove_correction(heard)
        self.heard_input.clear()
        self.written_input.clear()
        self.refresh()
        self.changed.emit()
        self.status.emit("Correction deleted")

    # ---- shared ---------------------------------------------------------

    def refresh(self) -> None:
        query = self.search.text().strip().lower()

        self.terms_list.clear()
        for term in self._dictionary.terms:
            if not query or query in term.lower():
                self.terms_list.addItem(term)

        self.corrections_table.setRowCount(0)
        for heard in sorted(self._dictionary.corrections, key=str.lower):
            written = self._dictionary.corrections[heard]
            if query and query not in heard.lower() and query not in written.lower():
                continue
            row = self.corrections_table.rowCount()
            self.corrections_table.insertRow(row)
            self.corrections_table.setItem(row, 0, QTableWidgetItem(heard))
            self.corrections_table.setItem(row, 1, QTableWidgetItem(written))
