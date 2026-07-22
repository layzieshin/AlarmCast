"""Client audio output via sounddevice."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Any

import numpy as np

from alarmcast.core.audio_format import CHANNELS, SAMPLE_RATE, SAMPLES_PER_FRAME

LOGGER = logging.getLogger(__name__)

_TEST_TONE_HZ = 440.0
_TEST_TONE_MS = 300


class AudioOutput:
    """Play PCM int16 mono frames with volume and mute."""

    def __init__(
        self,
        volume: float = 0.9,
        muted: bool = False,
        device_id: int | None = None,
    ) -> None:
        self._volume = max(0.0, min(1.0, volume))
        self._muted = muted
        self._device_id = device_id
        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=120)
        self._test_queue: queue.Queue[bytes] = queue.Queue(maxsize=32)
        self._stream: Any = None
        self._lock = threading.Lock()

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))

    def set_muted(self, muted: bool) -> None:
        self._muted = muted

    def set_device(self, device_id: int | None) -> None:
        self._device_id = device_id if device_id is not None and device_id >= 0 else None

    def start(self) -> None:
        sd = _import_sounddevice()
        if sd is None:
            raise RuntimeError("sounddevice package is not available")
        if self._stream is not None:
            return
        self._stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            device=self._device_id,
            blocksize=SAMPLES_PER_FRAME,
            callback=self._audio_callback,
        )
        self._stream.start()
        LOGGER.info("Audio output started")

    def stop(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.stop()
            self._stream.close()
        except Exception as exc:
            LOGGER.warning("Audio output stop failed: %s", exc)
        self._stream = None
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
            while not self._test_queue.empty():
                try:
                    self._test_queue.get_nowait()
                except queue.Empty:
                    break

    def play_test_tone(self) -> bool:
        """Play a short test beep at current volume (bypasses mute)."""
        if self._stream is None:
            worker = threading.Thread(
                target=_play_test_tone_direct,
                args=(self._device_id, self._volume),
                daemon=True,
                name="alarmcast-test-tone",
            )
            worker.start()
            return True
        for payload in build_test_tone_frames(self._volume):
            try:
                self._test_queue.put_nowait(payload)
            except queue.Full:
                break
        return True

    def enqueue(self, payload: bytes) -> None:
        if self._stream is None:
            return
        if self._queue.qsize() > 25:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            pass

    def _audio_callback(
        self, outdata: np.ndarray, frames: int, _time_info: Any, _status: Any
    ) -> None:
        from_test = False
        try:
            payload = self._test_queue.get_nowait()
            from_test = True
        except queue.Empty:
            try:
                payload = self._queue.get_nowait()
            except queue.Empty:
                outdata.fill(0)
                return

        if not from_test and self._muted:
            outdata.fill(0)
            return

        vol = 1.0 if from_test else self._volume
        if vol >= 0.999:
            mv = memoryview(outdata).cast("B")
            mv[: len(payload)] = payload
            if len(payload) < len(mv):
                mv[len(payload) :] = b"\x00" * (len(mv) - len(payload))
            return

        arr = np.frombuffer(payload, dtype=np.int16)
        scaled = np.clip(arr.astype(np.float32) * vol, -32768, 32767).astype(np.int16)
        pb = scaled.tobytes()
        mv = memoryview(outdata).cast("B")
        mv[: len(pb)] = pb
        if len(pb) < len(mv):
            mv[len(pb) :] = b"\x00" * (len(mv) - len(pb))


def build_test_tone_frames(volume: float) -> list[bytes]:
    """Build PCM frames for a short sine test tone at the given volume."""
    vol = max(0.0, min(1.0, volume))
    total_samples = int(SAMPLE_RATE * _TEST_TONE_MS / 1000.0)
    t = np.arange(total_samples, dtype=np.float32) / float(SAMPLE_RATE)
    wave = np.sin(2.0 * np.pi * _TEST_TONE_HZ * t) * vol
    pcm = np.clip(wave * 32767.0, -32768, 32767).astype(np.int16)
    frames: list[bytes] = []
    offset = 0
    while offset < pcm.size:
        chunk = pcm[offset : offset + SAMPLES_PER_FRAME]
        offset += SAMPLES_PER_FRAME
        if chunk.size < SAMPLES_PER_FRAME:
            padded = np.zeros(SAMPLES_PER_FRAME, dtype=np.int16)
            padded[: chunk.size] = chunk
            chunk = padded
        frames.append(chunk.tobytes())
    return frames


def _play_test_tone_direct(device_id: int | None, volume: float) -> None:
    """Play a short test tone via a temporary stream (works without active network)."""
    sd = _import_sounddevice()
    if sd is None:
        return
    raw = b"".join(build_test_tone_frames(volume))
    if not raw:
        return
    pcm16 = np.frombuffer(raw, dtype=np.int16)
    signal = pcm16.astype(np.float32) / 32767.0
    try:
        sd.play(signal, samplerate=SAMPLE_RATE, device=device_id)
        sd.wait()
    except Exception as exc:
        LOGGER.warning("Temporary test tone playback failed: %s", exc)


def _import_sounddevice() -> Any | None:
    try:
        import sounddevice

        return sounddevice
    except Exception:
        return None


def list_output_devices() -> list[tuple[int, str]]:
    """Return (device_id, label) for output devices."""
    sd = _import_sounddevice()
    if sd is None:
        return [(-1, "Standard (Windows)")]
    try:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
    except Exception:
        return [(-1, "Standard (Windows)")]
    result: list[tuple[int, str]] = [(-1, "Standard (Windows)")]
    for index, dev in enumerate(devices):
        if dev.get("max_output_channels", 0) > 0:
            hostapi_name = str(hostapis[int(dev["hostapi"])]["name"])
            label = _friendly_device_label(str(dev["name"]), hostapi_name)
            result.append((index, label))
    return result


def _friendly_device_label(device_name: str, hostapi_name: str) -> str:
    """Build short one-line labels for device dropdown."""
    compact_name = " ".join(device_name.split())
    compact_hostapi = " ".join(hostapi_name.split())
    if compact_hostapi.lower() in compact_name.lower():
        label = compact_name
    else:
        label = f"{compact_name} - {compact_hostapi}"
    if len(label) > 72:
        return f"{label[:69]}..."
    return label
