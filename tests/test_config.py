"""Tests for config load/save behavior."""

from __future__ import annotations

import json
from pathlib import Path

from alarmcast.core.config import (
    ClientConfig,
    HostConfig,
    load_client_config,
    load_host_config,
    save_client_config,
    save_host_config,
)


def test_load_host_config_creates_default_with_psk(tmp_path: Path) -> None:
    path = tmp_path / "host.json"
    cfg = load_host_config(path)
    assert isinstance(cfg, HostConfig)
    assert len(cfg.psk) >= 8
    assert cfg.autostart_with_windows is True
    assert cfg.auto_start_runtime is True
    assert path.exists()


def test_load_client_config_creates_default(tmp_path: Path) -> None:
    path = tmp_path / "client.json"
    cfg = load_client_config(path)
    assert isinstance(cfg, ClientConfig)
    assert cfg.volume == 0.9
    assert cfg.autostart_with_windows is True
    assert cfg.auto_connect is True
    assert cfg.message_overlay_enabled is True
    assert path.exists()


def test_save_and_reload_host_config(tmp_path: Path) -> None:
    path = tmp_path / "host.json"
    save_host_config(
        HostConfig(
            psk="MYTOKEN",
            threshold_rms=0.1,
            signal_target=3,
            window_seconds=5.0,
            tcp_port=50123,
        ),
        path,
    )
    loaded = load_host_config(path)
    assert loaded.psk == "MYTOKEN"
    assert loaded.signal_target == 3
    assert loaded.tcp_port == 50123


def test_load_host_config_new_flags(tmp_path: Path) -> None:
    path = tmp_path / "host.json"
    path.write_text(
        '{"psk": "x", "autostart_with_windows": true, "auto_start_runtime": true}',
        encoding="utf-8",
    )
    loaded = load_host_config(path)
    assert loaded.autostart_with_windows is True
    assert loaded.auto_start_runtime is True


def test_save_client_config_writes_json_shape(tmp_path: Path) -> None:
    path = tmp_path / "client.json"
    save_client_config(ClientConfig(host_addr="10.0.0.5", psk="abc"), path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["host_addr"] == "10.0.0.5"
    assert raw["psk"] == "abc"
