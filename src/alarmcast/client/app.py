"""Client mode Qt application entry."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from alarmcast.core.logging_setup import configure_logging
from alarmcast.core.single_instance import start_single_instance_server
from alarmcast.core.ui_theme import apply_app_theme
from alarmcast.client.ui import ClientWindow

LOGGER = logging.getLogger(__name__)


def run() -> int:
    """Run the client mode app."""
    configure_logging()
    app = QApplication.instance() or QApplication(sys.argv)
    if isinstance(app, QApplication):
        app.setQuitOnLastWindowClosed(False)
        apply_app_theme(app)

    window = ClientWindow()
    start_single_instance_server(window._show_window)
    window.show()
    LOGGER.info("Client app started")
    return int(app.exec())
