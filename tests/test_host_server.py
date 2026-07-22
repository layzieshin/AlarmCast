"""Tests for host server helper logic."""

from __future__ import annotations

from alarmcast.host.server import _parse_hello


def test_parse_hello_valid_payload() -> None:
    parsed = _parse_hello(b"HELLO:DocPC:SECRET123\n")
    assert parsed == ("DocPC", "SECRET123")


def test_parse_hello_rejects_invalid_payload() -> None:
    assert _parse_hello(b"HELLO:OnlyName\n") is None
    assert _parse_hello(b"WRONG:DocPC:SECRET\n") is None
