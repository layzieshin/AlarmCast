"""TCP framing and thread-safe sending helpers."""

from __future__ import annotations

import socket
import struct
import threading
from dataclasses import dataclass
from typing import Literal

from alarmcast.core.audio_format import BYTES_PER_FRAME

MessageMode = Literal["status", "info", "request"]

TCP_PORT = 50050

FT_AUDIO = b"A"
FT_CTRL = b"C"
FT_HELLO = b"H"

ALM_ON = b"ALM:1\n"
ALM_OFF = b"ALM:0\n"
ALM_RST = b"RST\n"

MSG_PREFIX = b"MSG:"
MSG_MAX_TEXT_BYTES = 200
_MODE_TO_CODE: dict[MessageMode, bytes] = {
    "status": b"0",
    "info": b"1",
    "request": b"2",
}
_CODE_TO_MODE: dict[bytes, MessageMode] = {
    b"0": "status",
    b"1": "info",
    b"2": "request",
}


@dataclass(frozen=True)
class HostMessage:
    """Host-to-client text message with display mode."""

    text: str
    mode: MessageMode = "status"


_HEADER = struct.Struct("<cI")


@dataclass
class Frame:
    """One framed protocol message."""

    ftype: bytes
    payload: bytes


class LockedSender:
    """Serialize all send operations for one socket."""

    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._lock = threading.Lock()

    def send_frame(self, ftype: bytes, payload: bytes) -> bool:
        """Send one frame using the internal lock."""
        return send_frame(self._sock, ftype, payload, lock=self._lock)


def send_frame(
    sock: socket.socket,
    ftype: bytes,
    payload: bytes,
    lock: threading.Lock | None = None,
) -> bool:
    """Send one framed message. Returns False on socket error."""
    if len(ftype) != 1:
        raise ValueError("ftype must be exactly one byte")
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")

    data = _HEADER.pack(ftype, len(payload))
    if lock is None:
        try:
            sock.sendall(data)
            if payload:
                sock.sendall(payload)
            return True
        except OSError:
            return False

    with lock:
        try:
            sock.sendall(data)
            if payload:
                sock.sendall(payload)
            return True
        except OSError:
            return False


def recv_frame(sock: socket.socket) -> Frame | None:
    """Read exactly one frame, or None if disconnected/error."""
    header = _recv_exact(sock, _HEADER.size)
    if header is None:
        return None

    ftype, length = _HEADER.unpack(header)
    payload = b""
    if length:
        payload_or_none = _recv_exact(sock, length)
        if payload_or_none is None:
            return None
        payload = payload_or_none
    return Frame(ftype=ftype, payload=payload)


def is_audio_frame_valid(payload: bytes) -> bool:
    """Validate fixed-size audio payloads."""
    return len(payload) == BYTES_PER_FRAME


def encode_message(text: str, mode: MessageMode = "status") -> bytes:
    """Build a host-to-client broadcast message control payload."""
    cleaned = text.strip().replace("\n", " ").replace("\r", " ")
    encoded = cleaned.encode("utf-8")[:MSG_MAX_TEXT_BYTES]
    mode_code = _MODE_TO_CODE.get(mode, b"0")
    return MSG_PREFIX + mode_code + b":" + encoded + b"\n"


def parse_message(payload: bytes) -> HostMessage | None:
    """Parse MSG control payload; returns None if not a message frame."""
    if not payload.startswith(MSG_PREFIX):
        return None
    body = payload[len(MSG_PREFIX) :]
    if body.endswith(b"\n"):
        body = body[:-1]

    mode: MessageMode = "status"
    text_bytes = body
    if len(body) >= 2 and body[1:2] == b":" and body[0:1] in _CODE_TO_MODE:
        mode = _CODE_TO_MODE[body[0:1]]
        text_bytes = body[2:]

    try:
        text = text_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None
    if not text:
        return None
    return HostMessage(text=text, mode=mode)


def _recv_exact(sock: socket.socket, num_bytes: int) -> bytes | None:
    """Read exactly num_bytes. Timeout is retried, EOF returns None."""
    buffer = bytearray()
    while len(buffer) < num_bytes:
        try:
            chunk = sock.recv(num_bytes - len(buffer))
        except socket.timeout:
            continue
        except OSError:
            return None
        if not chunk:
            return None
        buffer.extend(chunk)
    return bytes(buffer)
