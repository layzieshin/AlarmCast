"""Tests for PSK helpers."""

from __future__ import annotations

import pytest

from alarmcast.core.security import generate_psk, verify_psk


def test_generate_psk_length() -> None:
    token = generate_psk(32)
    assert len(token) == 32


def test_generate_psk_rejects_too_short_length() -> None:
    with pytest.raises(ValueError):
        generate_psk(4)


def test_verify_psk_uses_trimmed_strings() -> None:
    assert verify_psk("ABC123", " ABC123 ")
    assert not verify_psk("ABC123", "XYZ999")
