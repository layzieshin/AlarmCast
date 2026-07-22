"""Multi-monitor warning overlay for client mode."""

from __future__ import annotations

import logging
import math

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QStyle, QWidget

LOGGER = logging.getLogger(__name__)

_OVERLAY_SIZE = 88
_MARGIN = 20
_PULSE_TICK_MS = 16
_PULSE_CYCLE_MS = 1400


def _warning_pixmap(size: int) -> QPixmap:
    """Load the standard warning icon at the given size (transparent background)."""
    style = QApplication.style()
    if style is None:
        return QPixmap()
    icon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
    return icon.pixmap(size, size)


class _WarningWidget(QWidget):
    """Frameless topmost widget showing the system warning icon."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(_OVERLAY_SIZE, _OVERLAY_SIZE)
        self._pixmap = _warning_pixmap(_OVERLAY_SIZE)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

    def set_blink_opacity(self, opacity: float) -> None:
        self._opacity_effect.setOpacity(opacity)

    def paintEvent(self, _event: object) -> None:
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        x = (self.width() - self._pixmap.width()) // 2
        y = (self.height() - self._pixmap.height()) // 2
        painter.drawPixmap(QPoint(x, y), self._pixmap)


class WarningOverlayManager:
    """Manage one overlay per screen."""

    def __init__(self) -> None:
        self._windows: list[_WarningWidget] = []
        self._active = False
        self._phase = -math.pi / 2.0
        self._timer = QTimer()
        self._timer.setInterval(_PULSE_TICK_MS)
        self._timer.timeout.connect(self._pulse_tick)
        self._create_windows()

    def _create_windows(self) -> None:
        for win in self._windows:
            win.close()
        self._windows.clear()

        for screen in QGuiApplication.screens():
            geo = screen.availableGeometry()
            win = _WarningWidget()
            x = geo.x() + geo.width() - _OVERLAY_SIZE - _MARGIN
            y = geo.y() + _MARGIN
            win.move(x, y)
            win.hide()
            self._windows.append(win)

    def show(self) -> None:
        self._active = True
        self._phase = -math.pi / 2.0
        for win in self._windows:
            win.set_blink_opacity(0.0)
            win.show()
        if not self._timer.isActive():
            self._timer.start()

    def hide(self) -> None:
        self._active = False
        self._timer.stop()
        for win in self._windows:
            win.hide()

    def refresh_screens(self) -> None:
        was_active = self._active
        self._create_windows()
        if was_active:
            self.show()

    def _pulse_tick(self) -> None:
        if not self._active:
            return
        step = (2.0 * math.pi * _PULSE_TICK_MS) / _PULSE_CYCLE_MS
        self._phase += step
        opacity = (math.sin(self._phase) + 1.0) / 2.0
        for win in self._windows:
            win.set_blink_opacity(opacity)
