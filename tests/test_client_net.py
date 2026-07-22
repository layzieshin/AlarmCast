"""Tests for client network helpers."""

from __future__ import annotations

import socket

from alarmcast.client.net import ClientNetwork, HostEndpoint


def test_build_hello_payload_format() -> None:
    net = ClientNetwork(psk="SECRET", host_addr="127.0.0.1")
    sock_a, sock_b = socket.socketpair()
    try:
        assert net._send_hello(sock_a)  # noqa: SLF001 — internal helper under test
        from alarmcast.core.protocol import FT_HELLO, recv_frame

        frame = recv_frame(sock_b)
        assert frame is not None
        assert frame.ftype == FT_HELLO
        text = frame.payload.decode("ascii")
        assert text.startswith("HELLO:")
        assert text.endswith("\n")
        assert ":SECRET" in text
    finally:
        sock_a.close()
        sock_b.close()


def test_host_endpoint_dataclass() -> None:
    ep = HostEndpoint(host="10.0.0.5", port=50050)
    assert ep.host == "10.0.0.5"
    assert ep.port == 50050
