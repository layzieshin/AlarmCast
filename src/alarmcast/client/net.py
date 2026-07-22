"""Client TCP connection with mDNS discovery and auto-reconnect."""

from __future__ import annotations

import logging
import socket
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from alarmcast.core.discovery import browse_for_host
from alarmcast.core.protocol import (
    ALM_OFF,
    ALM_ON,
    ALM_RST,
    FT_AUDIO,
    FT_CTRL,
    FT_HELLO,
    TCP_PORT,
    HostMessage,
    is_audio_frame_valid,
    parse_message,
    recv_frame,
    send_frame,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class HostEndpoint:
    """Resolved host address and port."""

    host: str
    port: int


class ClientNetwork:
    """Maintain TCP connection to host with reconnect loop."""

    def __init__(
        self,
        psk: str,
        host_addr: str = "",
        host_port: int = TCP_PORT,
        on_audio: Callable[[bytes], None] | None = None,
        on_alarm_on: Callable[[], None] | None = None,
        on_alarm_off: Callable[[], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        on_message: Callable[[HostMessage], None] | None = None,
    ) -> None:
        self._psk = psk
        self._host_addr = host_addr.strip()
        self._host_port = host_port
        self._on_audio = on_audio
        self._on_alarm_on = on_alarm_on
        self._on_alarm_off = on_alarm_off
        self._on_status = on_status
        self._on_message = on_message

        self._running = False
        self._thread: threading.Thread | None = None
        self._sock: socket.socket | None = None
        self._sock_lock = threading.Lock()

    @property
    def connected(self) -> bool:
        with self._sock_lock:
            return self._sock is not None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._connect_loop, name="client-net", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._close_socket()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None

    def set_host_addr(self, host_addr: str, port: int = TCP_PORT) -> None:
        self._host_addr = host_addr.strip()
        self._host_port = port

    def set_psk(self, psk: str) -> None:
        self._psk = psk.strip()

    def send_reset(self) -> None:
        with self._sock_lock:
            sock = self._sock
        if sock is None:
            return
        send_frame(sock, FT_CTRL, ALM_RST)

    def _connect_loop(self) -> None:
        while self._running:
            endpoint = self._resolve_host()
            if endpoint is None:
                self._emit_status("Suche Host ...")
                time.sleep(2.0)
                continue

            try:
                self._emit_status(f"Verbinde mit {endpoint.host}:{endpoint.port} ...")
                sock = socket.create_connection((endpoint.host, endpoint.port), timeout=5.0)
                sock.settimeout(None)
            except OSError as exc:
                LOGGER.warning("Connection failed: %s", exc)
                self._emit_status("Verbindung fehlgeschlagen, erneuter Versuch ...")
                time.sleep(2.0)
                continue

            if not self._send_hello(sock):
                sock.close()
                self._emit_status("HELLO abgelehnt oder fehlgeschlagen")
                time.sleep(2.0)
                continue

            with self._sock_lock:
                self._sock = sock
            self._emit_status(f"Verbunden mit {endpoint.host}:{endpoint.port}")
            self._read_loop(sock)
            self._close_socket()
            self._emit_status("Verbindung verloren, reconnect ...")
            time.sleep(2.0)

    def _resolve_host(self) -> HostEndpoint | None:
        if self._host_addr:
            return HostEndpoint(host=self._host_addr, port=self._host_port)
        discovered = browse_for_host(timeout=2.0)
        if discovered is None:
            return None
        return HostEndpoint(host=discovered.host, port=discovered.port)

    def _send_hello(self, sock: socket.socket) -> bool:
        pcname = socket.gethostname()
        payload = f"HELLO:{pcname}:{self._psk}\n".encode("ascii", errors="ignore")
        return send_frame(sock, FT_HELLO, payload)

    def _read_loop(self, sock: socket.socket) -> None:
        while self._running:
            frame = recv_frame(sock)
            if frame is None:
                break
            if frame.ftype == FT_AUDIO:
                if is_audio_frame_valid(frame.payload) and self._on_audio is not None:
                    self._on_audio(frame.payload)
            elif frame.ftype == FT_CTRL:
                host_message = parse_message(frame.payload)
                if host_message is not None:
                    if self._on_message is not None:
                        self._on_message(host_message)
                elif frame.payload == ALM_ON and self._on_alarm_on is not None:
                    self._on_alarm_on()
                elif frame.payload == ALM_OFF and self._on_alarm_off is not None:
                    self._on_alarm_off()

    def _close_socket(self) -> None:
        with self._sock_lock:
            sock = self._sock
            self._sock = None
        if sock is None:
            return
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass

    def _emit_status(self, text: str) -> None:
        if self._on_status is not None:
            self._on_status(text)
