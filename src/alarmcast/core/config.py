"""Configuration I/O in %APPDATA%\\AlarmCast."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from alarmcast.core.protocol import TCP_PORT
from alarmcast.core.security import generate_psk

APP_NAME = "AlarmCast"
HOST_CONFIG_NAME = "host.json"
CLIENT_CONFIG_NAME = "client.json"


@dataclass
class HostConfig:
    """Host runtime configuration."""

    psk: str
    threshold_rms: float = 0.06
    signal_target: int = 2
    window_seconds: float = 3.0
    tcp_port: int = TCP_PORT
    autostart_with_windows: bool = True
    auto_start_runtime: bool = True


@dataclass
class ClientConfig:
    """Client runtime configuration."""

    host_addr: str = ""
    psk: str = ""
    volume: float = 0.9
    muted: bool = False
    output_device_id: int = -1
    autostart_with_windows: bool = True
    auto_connect: bool = True
    message_overlay_enabled: bool = True


def get_config_dir() -> Path:
    """Return and create the app config directory."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        path = Path(appdata) / APP_NAME
    else:
        path = Path.home() / "AppData" / "Roaming" / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_host_config(path_override: Path | None = None) -> HostConfig:
    """Load host configuration or create defaults."""
    path = path_override or (get_config_dir() / HOST_CONFIG_NAME)
    if not path.exists():
        cfg = HostConfig(psk=generate_psk())
        save_host_config(cfg, path)
        return cfg

    raw = _read_json(path)
    cfg = HostConfig(
        psk=str(raw.get("psk") or generate_psk()),
        threshold_rms=_as_float(raw.get("threshold_rms"), 0.06),
        signal_target=_as_int(raw.get("signal_target"), 2),
        window_seconds=_as_float(raw.get("window_seconds"), 3.0),
        tcp_port=_as_int(raw.get("tcp_port"), TCP_PORT),
        autostart_with_windows=bool(raw.get("autostart_with_windows", True)),
        auto_start_runtime=bool(raw.get("auto_start_runtime", True)),
    )
    save_host_config(cfg, path)
    return cfg


def save_host_config(cfg: HostConfig, path_override: Path | None = None) -> Path:
    """Persist host config as JSON."""
    path = path_override or (get_config_dir() / HOST_CONFIG_NAME)
    _write_json(path, asdict(cfg))
    return path


def load_client_config(path_override: Path | None = None) -> ClientConfig:
    """Load client configuration or create defaults."""
    path = path_override or (get_config_dir() / CLIENT_CONFIG_NAME)
    if not path.exists():
        cfg = ClientConfig()
        save_client_config(cfg, path)
        return cfg

    raw = _read_json(path)
    cfg = ClientConfig(
        host_addr=str(raw.get("host_addr", "")),
        psk=str(raw.get("psk", "")),
        volume=_as_float(raw.get("volume"), 0.9),
        muted=bool(raw.get("muted", False)),
        output_device_id=_as_int(raw.get("output_device_id"), -1),
        autostart_with_windows=bool(raw.get("autostart_with_windows", True)),
        auto_connect=bool(raw.get("auto_connect", True)),
        message_overlay_enabled=bool(raw.get("message_overlay_enabled", True)),
    )
    save_client_config(cfg, path)
    return cfg


def save_client_config(cfg: ClientConfig, path_override: Path | None = None) -> Path:
    """Persist client config as JSON."""
    path = path_override or (get_config_dir() / CLIENT_CONFIG_NAME)
    _write_json(path, asdict(cfg))
    return path


def _read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Config file is not an object: {path}")
    return data


def _write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def _as_float(value: object, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _as_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default
