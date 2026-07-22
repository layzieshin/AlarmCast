"""Tests for host capture helpers."""

from __future__ import annotations

import numpy as np

from unittest.mock import MagicMock

from alarmcast.host.capture import _float_to_pcm16_mono_bytes, _get_loopback_microphone


def test_get_loopback_microphone_uses_speaker_id_with_include_loopback() -> None:
    soundcard = MagicMock()
    speaker = MagicMock(name="Speakers", id="device-id-1")
    soundcard.default_speaker.return_value = speaker
    loopback_mic = MagicMock(name="Speakers loopback")
    soundcard.get_microphone.return_value = loopback_mic

    result = _get_loopback_microphone(soundcard)

    soundcard.get_microphone.assert_called_once_with(id="device-id-1", include_loopback=True)
    assert result is loopback_mic


def test_float_to_pcm16_uses_first_channel_for_stereo() -> None:
    stereo = np.array([[0.5, -0.2], [-0.5, 0.3]], dtype=np.float32)
    payload = _float_to_pcm16_mono_bytes(stereo)
    arr = np.frombuffer(payload, dtype=np.int16)
    assert arr.tolist() == [16383, -16383]
