"""Pure alarm detection logic based on RMS threshold crossings."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic
from typing import Callable


class AlarmEvent(str, Enum):
    """State transitions emitted by the detector."""

    NONE = "none"
    ACTIVATED = "activated"
    CLEARED = "cleared"


@dataclass
class AlarmState:
    """Current detector state for diagnostics and tests."""

    alarm_active: bool
    signal_count: int
    window_remaining_seconds: float
    above_threshold: bool


class AlarmDetector:
    """Detect a target amount of threshold crossings in a time window."""

    def __init__(
        self,
        threshold: float,
        signal_target: int,
        window_seconds: float,
        time_fn: Callable[[], float] | None = None,
        release_factor: float = 0.7,
    ) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be > 0")
        if signal_target < 1:
            raise ValueError("signal_target must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        if not (0 < release_factor < 1):
            raise ValueError("release_factor must be between 0 and 1")

        self.threshold = threshold
        self.signal_target = signal_target
        self.window_seconds = window_seconds
        self.release_factor = release_factor
        self._time_fn = time_fn or monotonic

        self._alarm_active = False
        self._signal_count = 0
        self._window_start: float | None = None
        self._above_threshold = False

    def update(self, rms: float) -> AlarmEvent:
        """Process one RMS sample and emit state transition events."""
        rising_edge = self._is_rising_edge(rms)
        self._update_above_threshold(rms)
        if self._alarm_active:
            return AlarmEvent.NONE

        if self._is_window_expired():
            self._reset_window()

        if rising_edge:
            self._register_signal()
            if self._signal_count >= self.signal_target:
                self._alarm_active = True
                return AlarmEvent.ACTIVATED
        return AlarmEvent.NONE

    def reset(self) -> AlarmEvent:
        """Reset detector state after a user-triggered reset."""
        had_alarm = self._alarm_active
        self._alarm_active = False
        self._reset_window()
        self._above_threshold = False
        return AlarmEvent.CLEARED if had_alarm else AlarmEvent.NONE

    def snapshot(self) -> AlarmState:
        """Return a snapshot of the current detector state."""
        remaining = 0.0
        if self._window_start is not None:
            elapsed = self._time_fn() - self._window_start
            remaining = max(0.0, self.window_seconds - elapsed)
        return AlarmState(
            alarm_active=self._alarm_active,
            signal_count=self._signal_count,
            window_remaining_seconds=remaining,
            above_threshold=self._above_threshold,
        )

    def _is_window_expired(self) -> bool:
        if self._window_start is None:
            return False
        return (self._time_fn() - self._window_start) > self.window_seconds

    def _is_rising_edge(self, rms: float) -> bool:
        return (not self._above_threshold) and rms >= self.threshold

    def _register_signal(self) -> None:
        now = self._time_fn()
        if self._window_start is None:
            self._window_start = now
            self._signal_count = 1
            return
        self._signal_count += 1

    def _reset_window(self) -> None:
        self._signal_count = 0
        self._window_start = None

    def _update_above_threshold(self, rms: float) -> None:
        if self._above_threshold:
            release_threshold = self.threshold * self.release_factor
            if rms <= release_threshold:
                self._above_threshold = False
            return
        if rms >= self.threshold:
            self._above_threshold = True
