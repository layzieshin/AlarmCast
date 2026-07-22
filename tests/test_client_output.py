"""Tests for client audio output scaling."""

from __future__ import annotations

import numpy as np

from alarmcast.client.output import AudioOutput, build_test_tone_frames


def test_audio_output_volume_and_mute_flags() -> None:
    out = AudioOutput(volume=0.5, muted=True)
    out.set_volume(0.8)
    out.set_muted(False)
    assert out._volume == 0.8  # noqa: SLF001
    assert out._muted is False  # noqa: SLF001


def test_build_test_tone_frames_non_empty() -> None:
    frames = build_test_tone_frames(0.5)
    assert len(frames) >= 1
    assert all(len(frame) == 960 * 2 for frame in frames)


def test_scaled_audio_via_callback_shape() -> None:
    samples = np.full(960, 1000, dtype=np.int16)
    payload = samples.tobytes()
    out = AudioOutput(volume=0.5, muted=False)
    outdata = np.zeros((960, 1), dtype=np.int16)
    out._volume = 0.5
    out._muted = False
    out._audio_callback(outdata, 960, None, None)
    out._queue.put_nowait(payload)
    out._audio_callback(outdata, 960, None, None)
    assert outdata[0, 0] == 500
