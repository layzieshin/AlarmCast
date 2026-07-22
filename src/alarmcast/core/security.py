"""Security helpers for host/client authentication."""

from __future__ import annotations

import base64
import hmac
import secrets


def generate_psk(length: int = 32) -> str:
    """Generate a human-safe pre-shared key."""
    if length < 8:
        raise ValueError("PSK length must be at least 8")
    raw = secrets.token_bytes(32)
    token = base64.b32encode(raw).decode("ascii").rstrip("=")
    return token[:length]


def verify_psk(expected: str, given: str) -> bool:
    """Verify two PSKs using constant-time comparison."""
    return hmac.compare_digest(expected.strip(), given.strip())
