"""Top-screen message banner overlay for client mode."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from alarmcast.core.protocol import HostMessage

LOGGER = logging.getLogger(__name__)

_BANNER_HEIGHT = 42
_TOP_MARGIN = 8
_INFO_DURATION_MS = 10_000
_BANNER_STYLE = (
    "background-color: rgba(223, 228, 234, 235);"
    "color: #1e1e1e;"
    "font-size: 9pt;"
    "border-bottom: 1px solid #a9b2bb;"
)


class MessageOverlayManager:
    """Show host messages as a top banner on the primary screen."""

    def __init__(self) -> None:
        self._window: _MessageBanner | None = None
        self._info_timer = QTimer()
        self._info_timer.setSingleShot(True)
        self._info_timer.timeout.connect(self._hide)
        self._pending: HostMessage | None = None
        self._request_active = False

    def show_message(self, message: HostMessage) -> None:
        """Display message according to mode (info timer or request confirm)."""
        if message.mode == "request":
            self._request_active = True
            self._info_timer.stop()
            self._show_banner(message, show_confirm=True)
            return

        if self._request_active:
            self._pending = message
            return

        if message.mode == "info":
            self._request_active = False
            self._show_banner(message, show_confirm=False)
            self._info_timer.start(_INFO_DURATION_MS)
            return

        self.hide()

    def hide(self) -> None:
        self._info_timer.stop()
        self._request_active = False
        self._pending = None
        if self._window is not None:
            self._window.hide()

    def _hide(self) -> None:
        if self._request_active:
            return
        self.hide()
        if self._pending is not None:
            pending = self._pending
            self._pending = None
            self.show_message(pending)

    def _confirm_request(self) -> None:
        self._request_active = False
        self.hide()
        if self._pending is not None:
            pending = self._pending
            self._pending = None
            self.show_message(pending)

    def _show_banner(self, message: HostMessage, *, show_confirm: bool) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            LOGGER.warning("No primary screen for message overlay")
            return

        geo = screen.geometry()
        if self._window is None:
            self._window = _MessageBanner(on_confirm=self._confirm_request)
        self._window.configure(message.text, show_confirm=show_confirm)
        width = geo.width()
        x = geo.x()
        y = geo.y() + _TOP_MARGIN
        self._window.setGeometry(x, y, width, _BANNER_HEIGHT)
        self._window.show()
        self._window.raise_()


class _MessageBanner(QWidget):
    """Frameless top banner with optional confirm button."""

    def __init__(self, on_confirm: object) -> None:
        super().__init__()
        self._on_confirm = on_confirm
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setStyleSheet(_BANNER_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        self._label = QLabel()
        self._label.setWordWrap(True)
        self._label.setFont(QFont("", 10))
        layout.addWidget(self._label, stretch=1)

        self._confirm_button = QPushButton("Bestaetigen")
        self._confirm_button.clicked.connect(self._on_confirm_clicked)
        layout.addWidget(self._confirm_button)

    def configure(self, text: str, *, show_confirm: bool) -> None:
        self._label.setText(text)
        self._confirm_button.setVisible(show_confirm)

    def _on_confirm_clicked(self) -> None:
        if callable(self._on_confirm):
            self._on_confirm()
