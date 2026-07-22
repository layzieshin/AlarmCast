"""Shared Qt stylesheet for Host and Client windows."""

from __future__ import annotations

APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f4f5f7;
    color: #1e1e1e;
    font-size: 10pt;
}
QTabWidget::pane {
    border: 1px solid #d0d4dc;
    border-radius: 6px;
    background: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background: #e8eaee;
    border: 1px solid #d0d4dc;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 12px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #ffffff;
    font-weight: bold;
}
QFrame#statusCard {
    background-color: #ffffff;
    border: 1px solid #d0d4dc;
    border-radius: 8px;
}
QFrame#alarmBanner {
    background-color: #fff8e1;
    border: 1px solid #ffd54f;
    border-radius: 8px;
}
QFrame#messageBanner {
    background-color: #e3f2fd;
    border: 1px solid #90caf9;
    border-radius: 8px;
}
QLabel#statusTitle {
    font-size: 12pt;
    font-weight: bold;
}
QLabel#statusDot {
    min-width: 14px;
    max-width: 14px;
    min-height: 14px;
    max-height: 14px;
    border-radius: 7px;
}
QListWidget {
    background: #ffffff;
    border: 1px solid #d0d4dc;
    border-radius: 6px;
}
QPushButton {
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid #b0b8c4;
    background: #ffffff;
}
QPushButton:hover {
    background: #eef1f5;
}
QPushButton:disabled {
    color: #9aa3b0;
    background: #f0f1f3;
}
QPushButton#primaryButton {
    background-color: #f9a825;
    border-color: #f57f17;
    font-weight: bold;
}
QPushButton#primaryButton:hover {
    background-color: #ffb300;
}
QPushButton#primaryButton:disabled {
    background-color: #ffe082;
    color: #8d6e00;
}
QPushButton#muteButton:checked {
    background-color: #ffcdd2;
    border-color: #e57373;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #d0d4dc;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    margin: -5px 0;
    background: #f9a825;
    border-radius: 8px;
}
QTableWidget {
    background: #ffffff;
    border: 1px solid #d0d4dc;
    border-radius: 6px;
    gridline-color: #e8eaee;
}
QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox {
    padding: 6px;
    border: 1px solid #c5cad3;
    border-radius: 4px;
    background: #ffffff;
}
"""


def apply_app_theme(app: object) -> None:
    """Apply shared stylesheet to a QApplication instance."""
    set_style = getattr(app, "setStyleSheet", None)
    if callable(set_style):
        set_style(APP_STYLESHEET)
