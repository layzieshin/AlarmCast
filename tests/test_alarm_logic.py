"""Tests for pure alarm detection logic."""

from __future__ import annotations

from alarmcast.core.alarm_logic import AlarmDetector, AlarmEvent


def test_alarm_activates_after_two_signals_in_window() -> None:
    now = [0.0]

    def fake_time() -> float:
        return now[0]

    detector = AlarmDetector(
        threshold=0.5,
        signal_target=2,
        window_seconds=3.0,
        time_fn=fake_time,
    )

    assert detector.update(0.1) == AlarmEvent.NONE
    assert detector.update(0.8) == AlarmEvent.NONE  # first rising edge
    assert detector.update(0.2) == AlarmEvent.NONE  # release

    now[0] = 1.2
    assert detector.update(0.9) == AlarmEvent.ACTIVATED  # second edge within window


def test_reset_clears_active_alarm() -> None:
    now = [0.0]

    def fake_time() -> float:
        return now[0]

    detector = AlarmDetector(
        threshold=0.5,
        signal_target=1,
        window_seconds=3.0,
        time_fn=fake_time,
    )
    assert detector.update(0.9) == AlarmEvent.ACTIVATED
    assert detector.reset() == AlarmEvent.CLEARED
    assert detector.snapshot().alarm_active is False


def test_window_expiration_resets_counter() -> None:
    now = [0.0]

    def fake_time() -> float:
        return now[0]

    detector = AlarmDetector(
        threshold=0.5,
        signal_target=2,
        window_seconds=3.0,
        time_fn=fake_time,
    )

    assert detector.update(0.9) == AlarmEvent.NONE
    assert detector.update(0.2) == AlarmEvent.NONE
    now[0] = 4.1
    assert detector.update(0.9) == AlarmEvent.NONE
    assert detector.snapshot().signal_count == 1
