"""Bridge between audio payloads and alarm detection events."""

from __future__ import annotations

import logging
from collections.abc import Callable

import numpy as np

from alarmcast.core.alarm_logic import AlarmDetector, AlarmEvent

LOGGER = logging.getLogger(__name__)


class HostDetector:
    """Process audio payloads and emit alarm on/off callbacks."""

    def __init__(
        self,
        threshold_rms: float,
        signal_target: int,
        window_seconds: float,
        on_alarm_on: Callable[[], None],
        on_alarm_off: Callable[[], None],
    ) -> None:
        self._detector = AlarmDetector(
            threshold=threshold_rms,
            signal_target=signal_target,
            window_seconds=window_seconds,
        )
        self._on_alarm_on = on_alarm_on
        self._on_alarm_off = on_alarm_off

    def process_audio_payload(self, payload: bytes) -> AlarmEvent:
        """Compute RMS from payload and update detector state."""
        if not payload:
            return AlarmEvent.NONE
        samples = np.frombuffer(payload, dtype=np.int16).astype(np.float32)
        if samples.size == 0:
            return AlarmEvent.NONE
        rms = float(np.sqrt(np.mean(np.square(samples)))) / 32768.0
        event = self._detector.update(rms)
        if event == AlarmEvent.ACTIVATED:
            LOGGER.info("Alarm activated [rms=%.4f]", rms)
            self._on_alarm_on()
        return event

    def reset(self) -> AlarmEvent:
        """Reset detector and emit alarm off callback when needed."""
        event = self._detector.reset()
        if event == AlarmEvent.CLEARED:
            LOGGER.info("Alarm cleared")
            self._on_alarm_off()
        return event
