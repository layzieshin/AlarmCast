"""Tests for TCP framing helpers."""

from __future__ import annotations

import socket
import threading

from alarmcast.core.protocol import (
    FT_CTRL,
    Frame,
    HostMessage,
    LockedSender,
    encode_message,
    parse_message,
    recv_frame,
    send_frame,
)


def test_send_and_receive_single_frame() -> None:
    sock_a, sock_b = socket.socketpair()
    try:
        assert send_frame(sock_a, FT_CTRL, b"PING\n")
        frame = recv_frame(sock_b)
        assert frame == Frame(ftype=FT_CTRL, payload=b"PING\n")
    finally:
        sock_a.close()
        sock_b.close()


def test_locked_sender_serializes_send_calls() -> None:
    sock_a, sock_b = socket.socketpair()
    try:
        sender = LockedSender(sock_a)

        def worker(payload: bytes) -> None:
            assert sender.send_frame(FT_CTRL, payload)

        t1 = threading.Thread(target=worker, args=(b"ONE\n",))
        t2 = threading.Thread(target=worker, args=(b"TWO\n",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        frame_1 = recv_frame(sock_b)
        frame_2 = recv_frame(sock_b)
        payloads = {frame_1.payload if frame_1 else b"", frame_2.payload if frame_2 else b""}
        assert payloads == {b"ONE\n", b"TWO\n"}
    finally:
        sock_a.close()
        sock_b.close()


def test_encode_and_parse_message_status_legacy() -> None:
    payload = encode_message("Wartung in 5 Min", mode="status")
    assert payload == b"MSG:0:Wartung in 5 Min\n"
    parsed = parse_message(payload)
    assert parsed == HostMessage(text="Wartung in 5 Min", mode="status")
    assert parse_message(b"ALM:1\n") is None


def test_parse_legacy_message_without_mode_code() -> None:
    assert parse_message(b"MSG:Wartung in 5 Min\n") == HostMessage(
        text="Wartung in 5 Min", mode="status"
    )


def test_encode_and_parse_info_and_request() -> None:
    info = parse_message(encode_message("Info text", mode="info"))
    assert info == HostMessage(text="Info text", mode="info")
    req = parse_message(encode_message("Bitte bestaetigen", mode="request"))
    assert req == HostMessage(text="Bitte bestaetigen", mode="request")


def test_encode_message_strips_newlines_and_limits_length() -> None:
    payload = encode_message("Zeile1\nZeile2", mode="status")
    assert parse_message(payload) == HostMessage(text="Zeile1 Zeile2", mode="status")


def test_recv_frame_returns_none_on_closed_socket() -> None:
    sock_a, sock_b = socket.socketpair()
    try:
        sock_a.close()
        assert recv_frame(sock_b) is None
    finally:
        sock_b.close()
