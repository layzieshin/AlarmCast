"""Host audio capture via soundcard WASAPI loopback."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

import numpy as np

from alarmcast.core.audio_format import CHANNELS, SAMPLE_RATE, SAMPLES_PER_FRAME

LOGGER = logging.getLogger(__name__)


class LoopbackCapture:
    """Capture host loopback audio and emit fixed-size PCM int16 frames."""

    def __init__(self, on_frame: Callable[[bytes], None]) -> None:
        self._on_frame = on_frame
        self._running = False
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        """Return whether capture loop is active."""
        return self._running

    def start(self) -> None:
        """Start background capture thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="loopback-capture", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop capture thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        soundcard = _import_soundcard()
        if soundcard is None:
            LOGGER.error("Capture failed: soundcard package is not available")
            self._running = False
            return

        try:
            loopback_mic = _get_loopback_microphone(soundcard)
        except Exception as exc:  # pragma: no cover - environment-dependent
            LOGGER.error("Capture setup failed: %s", exc)
            self._running = False
            return

        try:
            with loopback_mic.recorder(samplerate=SAMPLE_RATE, channels=CHANNELS) as recorder:
                LOGGER.info("Loopback capture started [device=%s]", loopback_mic.name)
                while self._running:
                    data = recorder.record(numframes=SAMPLES_PER_FRAME)
                    payload = _float_to_pcm16_mono_bytes(data)
                    self._on_frame(payload)
        except Exception as exc:  # pragma: no cover - environment-dependent
            LOGGER.error("Capture loop failed: %s", exc)
        finally:
            self._running = False
            LOGGER.info("Loopback capture stopped")


def _get_loopback_microphone(soundcard: Any) -> Any:
    """Return a soundcard microphone object for default speaker loopback."""
    speaker = soundcard.default_speaker()
    if speaker is None:
        raise RuntimeError("No default speaker found for loopback capture")

    loopback_mic = soundcard.get_microphone(id=str(speaker.id), include_loopback=True)
    if loopback_mic is None:
        loopback_mic = soundcard.get_microphone(speaker.name, include_loopback=True)

    if loopback_mic is None or not hasattr(loopback_mic, "recorder"):
        raise RuntimeError("No loopback capture device available (get_microphone include_loopback)")
    return loopback_mic


def _import_soundcard() -> Any | None:
    try:
        import soundcard

        return soundcard
    except Exception:
        return None


def _float_to_pcm16_mono_bytes(data: np.ndarray) -> bytes:
    if data.ndim == 2 and data.shape[1] > 1:
        data = data[:, 0]
    mono = np.asarray(data, dtype=np.float32)
    pcm = np.clip(mono * 32767.0, -32768, 32767).astype(np.int16)
    payload: bytes = pcm.tobytes()
    return payload
