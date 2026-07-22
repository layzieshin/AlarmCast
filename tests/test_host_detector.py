"""Tests for host detector bridge logic."""

from __future__ import annotations

import numpy as np

from alarmcast.core.alarm_logic import AlarmEvent
from alarmcast.host.detector import HostDetector


def _pcm_payload(amplitude: float) -> bytes:
    value = int(max(-1.0, min(1.0, amplitude)) * 32767)
    samples = np.full(960, value, dtype=np.int16)
    return samples.tobytes()


def test_host_detector_emits_alarm_on() -> None:
    on_calls: list[str] = []
    off_calls: list[str] = []
    detector = HostDetector(
        threshold_rms=0.2,
        signal_target=1,
        window_seconds=3.0,
        on_alarm_on=lambda: on_calls.append("on"),
        on_alarm_off=lambda: off_calls.append("off"),
    )
    event = detector.process_audio_payload(_pcm_payload(0.7))
    assert event == AlarmEvent.ACTIVATED
    assert on_calls == ["on"]
    assert off_calls == []


def test_host_detector_reset_emits_alarm_off() -> None:
    off_calls: list[str] = []
    detector = HostDetector(
        threshold_rms=0.2,
        signal_target=1,
        window_seconds=3.0,
        on_alarm_on=lambda: None,
        on_alarm_off=lambda: off_calls.append("off"),
    )
    detector.process_audio_payload(_pcm_payload(0.7))
    assert detector.reset() == AlarmEvent.CLEARED
    assert off_calls == ["off"]
