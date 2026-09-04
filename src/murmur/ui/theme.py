"""Turns the design tokens into a Qt stylesheet.

Nothing in here invents a value. Every number and colour comes from
tokens.py. If you need something new, add it there first.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QLinearGradient

from .tokens import BORDER, COLOUR as C, RADIUS, SIZE, SPACE, TYPE


def brushed(x1: float, y1: float, x2: float, y2: float) -> str:
    """A brushed aluminium gradient, as a Qt stylesheet value."""
    return (
        f"qlineargradient(x1:{x1}, y1:{y1}, x2:{x2}, y2:{y2}, "
        f"stop:0 {C.alu_light}, stop:0.45 {C.alu}, "
        f"stop:0.55 {C.alu}, stop:1 {C.alu_dark})"
    )


def plate_gradient() -> QLinearGradient:
    """The same metal, for hand painted widgets."""
    gradient = QLinearGradient(0, 0, 0, 1)
    gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
    gradient.setColorAt(0.0, QColor(C.alu_light))
    gradient.setColorAt(0.45, QColor(C.alu))
    gradient.setColorAt(0.55, QColor(C.alu))
    gradient.setColorAt(1.0, QColor(C.alu_dark))
    return gradient


def silkscreen_font(size: int | None = None, bold: bool = True) -> QFont:
    """Small, uppercase, tightly tracked. The printed label look."""
    font = QFont()
    font.setFamilies(["Inter", "Segoe UI", "Helvetica Neue", "Arial"])
    font.setPointSize(size or TYPE.size_label)
    font.setWeight(QFont.DemiBold if bold else QFont.Normal)
    font.setCapitalization(QFont.AllUppercase)
    font.setLetterSpacing(QFont.PercentageSpacing, 100 + TYPE.track_label * 100)
    return font


def mono_font(size: int | None = None) -> QFont:
    """Counters and timings. Digits must not jump."""
    font = QFont()
    font.setFamilies(["Cascadia Mono", "Consolas", "DejaVu Sans Mono", "Courier New"])
    font.setPointSize(size or TYPE.size_body)
    font.setLetterSpacing(QFont.PercentageSpacing, 100 + TYPE.track_mono * 100)
    return font


def body_font(size: int | None = None, bold: bool = False) -> QFont:
    font = QFont()
    font.setFamilies(["Inter", "Segoe UI", "Helvetica Neue", "Arial"])
    font.setPointSize(size or TYPE.size_body)
    font.setWeight(QFont.DemiBold if bold else QFont.Normal)
    return font


def qss() -> str:
    """The whole application stylesheet."""
    return f"""
/* ---------- shell ---------- */
QWidget {{
    background: {C.chassis};
    color: {C.ink};
    font-family: {TYPE.grotesque};
    font-size: {TYPE.size_body}pt;
}}
QMainWindow, QDialog {{ background: {C.chassis}; }}

QToolTip {{
    background: {C.panel};
    color: {C.ink};
    border: {BORDER.hairline}px solid {C.seam};
    padding: {SPACE.xs}px {SPACE.sm}px;
}}

/* ---------- panels: a surface with a seam around it ---------- */
QFrame#Panel {{
    background: {C.panel};
    border: {BORDER.hairline}px solid {C.seam};
    border-top-color: {C.bevel_light};
    border-radius: {RADIUS.none}px;
}}
QFrame#Well {{
    background: {C.panel_sunken};
    border: {BORDER.hairline}px solid {C.seam};
    border-top-color: {C.bevel_dark};
    border-bottom-color: {C.bevel_light};
    border-radius: {RADIUS.none}px;
}}
QFrame#Seam {{ background: {C.seam}; border: none; max-height: 1px; }}

/* ---------- silkscreen labels ---------- */
QLabel#Silk {{ color: {C.ink_dim}; background: transparent; }}
QLabel#SilkOnMetal {{ color: {C.ink_on_metal}; background: transparent; }}
QLabel#Hint {{ color: {C.ink_faint}; background: transparent; }}
QLabel#Warning {{
    color: {C.warning};
    background: transparent;
    padding: {SPACE.xs}px 0px;
}}

/* ---------- text sitting on the display glass ---------- */
/* The stylesheet outranks fonts set in code, so the sizes live here. */
QLabel#LCDText {{
    color: {C.lcd_text}; background: transparent;
    font-family: {TYPE.mono}; font-size: {TYPE.size_body}pt;
}}
QLabel#LCDBig {{
    color: {C.lcd_text}; background: transparent;
    font-family: {TYPE.mono}; font-size: {TYPE.size_counter}pt;
}}
QLabel#LCDDim {{
    color: {C.lcd_text_dim}; background: transparent;
    font-family: {TYPE.mono}; font-size: {TYPE.size_micro}pt;
}}

/* ---------- buttons: pressed, not tinted ---------- */
QPushButton {{
    background: {C.plastic_light};
    color: {C.ink};
    border: {BORDER.hairline}px solid {C.seam};
    border-top-color: {C.bevel_light};
    border-left-color: {C.bevel_light};
    border-bottom-color: {C.bevel_dark};
    border-right-color: {C.bevel_dark};
    border-radius: {RADIUS.sharp}px;
    min-height: {SIZE.button_h}px;
    min-width: {SIZE.button_min_w}px;
    padding: 0px {SPACE.md}px;
}}
QPushButton:hover {{ background: {C.alu_light}; border-top-color: {C.alu_edge}; }}
QPushButton:pressed {{
    background: {C.plastic_dark};
    border-top-color: {C.bevel_dark};
    border-left-color: {C.bevel_dark};
    border-bottom-color: {C.bevel_light};
    border-right-color: {C.bevel_light};
    padding-top: 1px;
}}
QPushButton:disabled {{ background: {C.plastic}; color: {C.ink_faint}; }}
QPushButton:focus {{ outline: none; border-color: {C.focus}; }}

QPushButton#Transport {{ min-height: {SIZE.transport_h}px; min-width: 116px; }}
QPushButton#TransportRec:checked {{
    background: {C.plastic_dark};
    color: {C.record};
    border-top-color: {C.bevel_dark};
    border-bottom-color: {C.bevel_light};
}}
QPushButton#Tiny {{
    min-width: 0px; min-height: 24px;
    padding: 0px {SPACE.sm}px;
    font-size: {TYPE.size_micro}pt;
}}

/* ---------- fields ---------- */
QLineEdit, QPlainTextEdit, QTextEdit {{
    background: {C.panel_sunken};
    color: {C.ink};
    border: {BORDER.hairline}px solid {C.seam};
    border-top-color: {C.bevel_dark};
    border-bottom-color: {C.bevel_light};
    border-radius: {RADIUS.sharp}px;
    min-height: {SIZE.field_h}px;
    padding: 0px {SPACE.sm}px;
    selection-background-color: {C.selection};
    selection-color: {C.ink};
}}
QLineEdit:focus, QPlainTextEdit:focus {{ border-color: {C.focus}; }}
QLineEdit::placeholder {{ color: {C.ink_faint}; }}

QComboBox {{
    background: {C.plastic_light};
    color: {C.ink};
    border: {BORDER.hairline}px solid {C.seam};
    border-top-color: {C.bevel_light};
    border-bottom-color: {C.bevel_dark};
    border-radius: {RADIUS.sharp}px;
    min-height: {SIZE.field_h}px;
    padding: 0px {SPACE.sm}px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
/* a plain triangle, drawn with borders so no image file is needed */
QComboBox::down-arrow {{
    image: none;
    width: 0px; height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {C.ink_dim};
    margin-right: {SPACE.xs}px;
}}
QComboBox::down-arrow:hover {{ border-top-color: {C.ink}; }}
QComboBox QAbstractItemView {{
    background: {C.panel};
    color: {C.ink};
    border: {BORDER.hairline}px solid {C.seam};
    selection-background-color: {C.selection};
}}

QCheckBox {{ background: transparent; spacing: {SPACE.sm}px; }}
QCheckBox::indicator {{
    width: 13px; height: 13px;
    background: {C.panel_sunken};
    border: {BORDER.hairline}px solid {C.seam};
    border-top-color: {C.bevel_dark};
}}
QCheckBox::indicator:checked {{ background: {C.accent}; }}

/* ---------- lists and tables ---------- */
QTableWidget, QTableView, QListWidget, QTreeWidget {{
    background: {C.panel_sunken};
    alternate-background-color: {C.chassis_raised};
    color: {C.ink};
    border: {BORDER.hairline}px solid {C.seam};
    border-top-color: {C.bevel_dark};
    gridline-color: {C.seam};
    outline: none;
}}
QTableWidget::item, QListWidget::item {{
    padding: {SPACE.xs}px {SPACE.sm}px;
    border: none;
}}
QTableWidget::item:selected, QListWidget::item:selected {{
    background: {C.selection};
    color: {C.ink};
}}
QHeaderView::section {{
    background: {brushed(0, 0, 0, 1)};
    color: {C.ink_on_metal};
    border: none;
    border-right: {BORDER.hairline}px solid {C.seam};
    border-bottom: {BORDER.hairline}px solid {C.seam};
    padding: {SPACE.xs}px {SPACE.sm}px;
    font-weight: {TYPE.weight_bold};
}}
QHeaderView {{ background: {C.chassis}; }}
QTableCornerButton::section {{ background: {C.alu_dark}; border: none; }}

/* ---------- tabs: panel selector ---------- */
QTabWidget::pane {{
    background: {C.panel};
    border: {BORDER.hairline}px solid {C.seam};
    border-top-color: {C.bevel_light};
    top: -1px;
}}
QTabBar {{ background: {C.chassis}; }}
QTabBar::tab {{
    background: {C.plastic};
    color: {C.ink_dim};
    border: {BORDER.hairline}px solid {C.seam};
    border-bottom: none;
    padding: {SPACE.sm}px {SPACE.lg}px;
    margin-right: 2px;
    min-width: 92px;
}}
QTabBar::tab:selected {{
    background: {brushed(0, 0, 0, 1)};
    color: {C.ink_on_metal};
    border-top-color: {C.alu_edge};
}}
QTabBar::tab:hover:!selected {{ background: {C.plastic_light}; color: {C.ink}; }}

/* ---------- menu bar ---------- */
QMenuBar {{
    background: {C.chassis_raised};
    color: {C.ink};
    border-bottom: {BORDER.hairline}px solid {C.seam};
    padding: 2px;
}}
QMenuBar::item {{ background: transparent; padding: {SPACE.xs}px {SPACE.md}px; }}
QMenuBar::item:selected {{ background: {C.selection}; }}
QMenu {{
    background: {C.panel};
    color: {C.ink};
    border: {BORDER.hairline}px solid {C.seam};
    padding: {SPACE.xs}px;
}}
QMenu::item {{ padding: {SPACE.xs}px {SPACE.xl}px {SPACE.xs}px {SPACE.md}px; }}
QMenu::item:selected {{ background: {C.selection}; }}
QMenu::separator {{ height: 1px; background: {C.seam}; margin: {SPACE.xs}px 0px; }}

/* ---------- scrollbars: thin, mechanical ---------- */
QScrollBar:vertical {{
    background: {C.chassis}; width: 11px; margin: 0px;
    border-left: {BORDER.hairline}px solid {C.seam};
}}
QScrollBar::handle:vertical {{
    background: {C.plastic_light}; min-height: 24px;
    border: {BORDER.hairline}px solid {C.seam};
}}
QScrollBar::handle:vertical:hover {{ background: {C.alu_dark}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0px; width: 0px; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar:horizontal {{
    background: {C.chassis}; height: 11px;
    border-top: {BORDER.hairline}px solid {C.seam};
}}
QScrollBar::handle:horizontal {{
    background: {C.plastic_light}; min-width: 24px;
    border: {BORDER.hairline}px solid {C.seam};
}}

QSplitter::handle {{ background: {C.seam}; }}
QStatusBar {{
    background: {C.chassis_raised};
    color: {C.ink_dim};
    border-top: {BORDER.hairline}px solid {C.seam};
}}
"""
