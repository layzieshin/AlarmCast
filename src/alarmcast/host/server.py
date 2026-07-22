"""Host TCP server for streaming audio and control frames."""

from __future__ import annotations

import logging
import socket
import threading
from dataclasses import dataclass
from itertools import count
from typing import Callable

from alarmcast.core.protocol import (
    ALM_RST,
    FT_CTRL,
    FT_HELLO,
    LockedSender,
    recv_frame,
)
from alarmcast.core.event_log import append_event
from alarmcast.core.security import verify_psk

LOGGER = logging.getLogger(__name__)


@dataclass
class _ClientConn:
    client_id: int
    name: str
    addr: str
    sock: socket.socket
    sender: LockedSender


class HostServer:
    """TCP server managing authenticated client connections."""

    def __init__(
        self,
        port: int,
        expected_psk: str,
        on_reset_request: Callable[[str], None] | None = None,
    ) -> None:
        self._port = port
        self._expected_psk = expected_psk
        self._on_reset_request = on_reset_request

        self._server_sock: socket.socket | None = None
        self._accept_thread: threading.Thread | None = None
        self._running = False

        self._clients: dict[int, _ClientConn] = {}
        self._clients_lock = threading.Lock()
        self._id_counter = count(1)

    @property
    def running(self) -> bool:
        """Return whether the server loop is active."""
        return self._running

    def start(self) -> None:
        """Start TCP listener and accept loop."""
        if self._running:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", self._port))
        sock.listen()
        sock.settimeout(1.0)
        self._server_sock = sock
        self._running = True
        self._accept_thread = threading.Thread(
            target=self._accept_loop, name="host-accept", daemon=True
        )
        self._accept_thread.start()
        LOGGER.info("Host server started [port=%s]", self._port)

    def stop(self) -> None:
        """Stop server and all client connections."""
        self._running = False
        if self._server_sock is not None:
            try:
                self._server_sock.close()
            except OSError:
                pass
            self._server_sock = None

        if self._accept_thread is not None:
            self._accept_thread.join(timeout=2.0)
            self._accept_thread = None

        with self._clients_lock:
            clients = list(self._clients.values())
            self._clients.clear()
        for client in clients:
            self._close_client_socket(client.sock)

        LOGGER.info("Host server stopped")

    def get_clients_snapshot(self) -> list[str]:
        """Return formatted client list entries."""
        with self._clients_lock:
            clients = list(self._clients.values())
        return [f"{c.name} ({c.addr})" for c in clients]

    def broadcast_audio(self, payload: bytes) -> None:
        """Broadcast one audio frame to all connected clients."""
        self._broadcast_frame(ftype=b"A", payload=payload)

    def broadcast_control(self, payload: bytes) -> None:
        """Broadcast one control frame to all connected clients."""
        self._broadcast_frame(ftype=FT_CTRL, payload=payload)

    def _broadcast_frame(self, ftype: bytes, payload: bytes) -> None:
        with self._clients_lock:
            clients = list(self._clients.values())
        dead_ids: list[int] = []
        for client in clients:
            if not client.sender.send_frame(ftype, payload):
                dead_ids.append(client.client_id)
        for client_id in dead_ids:
            self._drop_client(client_id)

    def _accept_loop(self) -> None:
        while self._running:
            server_sock = self._server_sock
            if server_sock is None:
                break
            try:
                conn, addr = server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(
                target=self._handle_new_client,
                args=(conn, addr),
                name="host-client-init",
                daemon=True,
            ).start()

    def _handle_new_client(self, conn: socket.socket, addr_tuple: tuple[str, int]) -> None:
        addr = f"{addr_tuple[0]}:{addr_tuple[1]}"
        conn.settimeout(5.0)
        hello = recv_frame(conn)
        if hello is None or hello.ftype != FT_HELLO:
            LOGGER.warning("Client rejected: missing HELLO [addr=%s]", addr)
            self._close_client_socket(conn)
            return

        parsed = _parse_hello(hello.payload)
        if parsed is None:
            LOGGER.warning("Client rejected: malformed HELLO [addr=%s]", addr)
            self._close_client_socket(conn)
            return

        name, psk = parsed
        if not verify_psk(self._expected_psk, psk):
            LOGGER.warning("Client rejected: invalid PSK [addr=%s name=%s]", addr, name)
            self._close_client_socket(conn)
            return

        conn.settimeout(None)
        client_id = next(self._id_counter)
        client = _ClientConn(
            client_id=client_id,
            name=name,
            addr=addr,
            sock=conn,
            sender=LockedSender(conn),
        )
        with self._clients_lock:
            self._clients[client_id] = client

        LOGGER.info("Client connected [name=%s addr=%s]", name, addr)
        append_event("client_connected", {"name": name, "addr": addr})
        threading.Thread(
            target=self._client_read_loop,
            args=(client_id,),
            name=f"host-client-read-{client_id}",
            daemon=True,
        ).start()

    def _client_read_loop(self, client_id: int) -> None:
        client = self._get_client(client_id)
        if client is None:
            return

        while self._running:
            frame = recv_frame(client.sock)
            if frame is None:
                break
            if (
                frame.ftype == FT_CTRL
                and frame.payload == ALM_RST
                and self._on_reset_request is not None
            ):
                self._on_reset_request(client.name)

        self._drop_client(client_id)

    def _get_client(self, client_id: int) -> _ClientConn | None:
        with self._clients_lock:
            return self._clients.get(client_id)

    def _drop_client(self, client_id: int) -> None:
        with self._clients_lock:
            client = self._clients.pop(client_id, None)
        if client is None:
            return
        self._close_client_socket(client.sock)
        LOGGER.info("Client disconnected [name=%s addr=%s]", client.name, client.addr)
        append_event("client_disconnected", {"name": client.name, "addr": client.addr})

    @staticmethod
    def _close_client_socket(sock: socket.socket) -> None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass


def _parse_hello(payload: bytes) -> tuple[str, str] | None:
    try:
        text = payload.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError:
        return None
    if not text.startswith("HELLO:"):
        return None
    rest = text.removeprefix("HELLO:")
    name, sep, psk = rest.rpartition(":")
    if sep == "" or not name or not psk:
        return None
    return name, psk
