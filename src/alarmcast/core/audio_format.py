"""Shared audio format constants for host and client."""

from __future__ import annotations

SAMPLE_RATE = 48_000
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2  # int16
FRAME_MS = 20

SAMPLES_PER_FRAME = SAMPLE_RATE * FRAME_MS // 1000
BYTES_PER_FRAME = SAMPLES_PER_FRAME * CHANNELS * SAMPLE_WIDTH_BYTES
