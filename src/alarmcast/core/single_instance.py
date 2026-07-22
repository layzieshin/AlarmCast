"""Ensure only one Alarmcast process runs per machine."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtNetwork import QLocalServer

LOGGER = logging.getLogger(__name__)

SERVER_NAME = "Alarmcast_v1"
_RAISE_CMD = b"raise"


def notify_existing_instance(*, server_name: str | None = None) -> bool:
    """Notify a running instance and return True if this process should exit.

    Avoids creating QCoreApplication before QApplication startup.
    """
    from PySide6.QtNetwork import QLocalSocket

    name = server_name or SERVER_NAME
    client = QLocalSocket()
    client.connectToServer(name)
    if client.waitForConnected(500):
        client.write(_RAISE_CMD)
        client.flush()
        client.waitForBytesWritten(1000)
        client.disconnectFromServer()
        LOGGER.info("Notified existing Alarmcast instance to raise window")
        return True
    return False


def start_single_instance_server(
    on_raise: Callable[[], None],
    *,
    server_name: str | None = None,
    allow_multiple: bool = False,
) -> bool:
    """Start the local server after QApplication exists. Returns False if skipped."""
    if allow_multiple:
        return True

    from PySide6.QtNetwork import QLocalServer

    name = server_name or SERVER_NAME
    server = QLocalServer()
    QLocalServer.removeServer(name)
    if not server.listen(name):
        LOGGER.warning("Could not start single-instance server: %s", server.errorString())
        return False

    holder = _InstanceServerHolder(server)
    holder.attach()
    holder.set_raise_callback(on_raise)
    LOGGER.debug("Single-instance server listening")
    return True


def acquire_or_notify_existing(
    *,
    allow_multiple: bool = False,
    server_name: str | None = None,
) -> bool:
    """Return True if this process should start the UI; False if another instance was notified.

    Deprecated for GUI startup: use notify_existing_instance() before QApplication,
    then start_single_instance_server() after QApplication is created.
    """
    if allow_multiple:
        return True
    if notify_existing_instance(server_name=server_name):
        return False
    return True


class _InstanceServerHolder:
    """Keep the local server alive and route raise requests."""

    _instance: _InstanceServerHolder | None = None

    def __init__(self, server: QLocalServer) -> None:
        self._server = server
        self._raise_callback: Callable[[], None] | None = None

    def attach(self) -> None:
        _InstanceServerHolder._instance = self
        self._server.newConnection.connect(self._on_new_connection)

    def set_raise_callback(self, callback: Callable[[], None]) -> None:
        self._raise_callback = callback

    def _on_new_connection(self) -> None:
        socket = self._server.nextPendingConnection()
        if socket is None:
            return
        if socket.waitForReadyRead(500):
            data = bytes(socket.readAll().data())
            if data.strip() == _RAISE_CMD:
                LOGGER.info("Raise window requested by second instance")
                if self._raise_callback is not None:
                    self._raise_callback()
        socket.disconnectFromServer()


def register_raise_window(callback: Callable[[], None]) -> None:
    """Register UI callback to show the main window when a second instance starts."""
    holder = _InstanceServerHolder._instance
    if holder is not None:
        holder.set_raise_callback(callback)
