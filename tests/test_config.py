"""Tests for versioned, atomic configuration persistence."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import pytest

from alarmcast.core import config as config_module
from alarmcast.core.config import (
    SCHEMA_VERSION,
    ClientConfig,
    ConfigRecoveryError,
    ConfigWriteError,
    HostConfig,
    InvalidConfigVersionError,
    UnsupportedConfigVersionError,
    load_client_config,
    load_host_config,
    save_client_config,
    save_host_config,
)
from alarmcast.core.protocol import TCP_PORT

Config = HostConfig | ClientConfig
Loader = Callable[[Path | None], Config]
Saver = Callable[[Config, Path | None], Path]


def _backup(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak")


def _read(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _host() -> HostConfig:
    return HostConfig(
        psk="TEST-HOST-PSK",
        threshold_rms=0.125,
        signal_target=4,
        window_seconds=6.5,
        tcp_port=50123,
        autostart_with_windows=False,
        auto_start_runtime=False,
    )


def _client() -> ClientConfig:
    return ClientConfig(
        host_addr="192.0.2.5",
        psk="TEST-CLIENT-PSK",
        volume=0.35,
        muted=True,
        output_device_id=7,
        autostart_with_windows=False,
        auto_connect=False,
        message_overlay_enabled=False,
    )


CONFIG_CASES: tuple[tuple[str, Loader, Saver, Callable[[], Config]], ...] = (
    ("host", load_host_config, save_host_config, _host),
    ("client", load_client_config, save_client_config, _client),
)


@pytest.mark.parametrize(("name", "loader", "_saver", "_factory"), CONFIG_CASES)
def test_first_start_creates_versioned_primary_and_backup(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    _factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"

    loaded = loader(path)

    assert isinstance(loaded, HostConfig if name == "host" else ClientConfig)
    if isinstance(loaded, HostConfig):
        assert len(loaded.psk) >= 8
    primary = _read(path)
    backup = _read(_backup(path))
    assert primary["schema_version"] == SCHEMA_VERSION
    assert backup == primary
    assert path.read_bytes().endswith(b"\n")
    assert _backup(path).read_bytes().endswith(b"\n")


@pytest.mark.parametrize(("name", "loader", "saver", "factory"), CONFIG_CASES)
def test_roundtrip_all_known_fields(
    tmp_path: Path,
    name: str,
    loader: Loader,
    saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    expected = factory()

    saver(expected, path)

    assert loader(path) == expected
    assert _read(path) == {"schema_version": SCHEMA_VERSION, **asdict(expected)}
    assert _read(_backup(path)) == _read(path)


@pytest.mark.parametrize(("name", "loader", "_saver", "factory"), CONFIG_CASES)
def test_unversioned_configuration_is_migrated(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    expected = factory()
    path.write_text(json.dumps(asdict(expected)), encoding="utf-8")

    assert loader(path) == expected
    assert _read(path) == {"schema_version": SCHEMA_VERSION, **asdict(expected)}
    assert _read(_backup(path)) == _read(path)


@pytest.mark.parametrize(("name", "loader", "_saver", "_factory"), CONFIG_CASES)
def test_migration_supplies_existing_defaults_for_missing_fields(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    _factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    legacy = {"psk": "LEGACY-PSK"} if name == "host" else {"host_addr": "example.test"}
    path.write_text(json.dumps(legacy), encoding="utf-8")

    loaded = loader(path)

    if isinstance(loaded, HostConfig):
        assert loaded.threshold_rms == 0.06
        assert loaded.signal_target == 2
        assert loaded.tcp_port == TCP_PORT
        assert loaded.autostart_with_windows is True
        assert loaded.auto_start_runtime is True
    else:
        assert loaded.volume == 0.9
        assert loaded.output_device_id == -1
        assert loaded.autostart_with_windows is True
        assert loaded.auto_connect is True
        assert loaded.message_overlay_enabled is True
    assert _read(path)["schema_version"] == SCHEMA_VERSION


@pytest.mark.parametrize(("name", "loader", "_saver", "factory"), CONFIG_CASES)
def test_migration_preserves_unknown_top_level_fields(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    legacy = {**asdict(factory()), "future_option": {"enabled": True}, "extension": [1, 2]}
    path.write_text(json.dumps(legacy), encoding="utf-8")

    loader(path)

    stored = _read(path)
    assert stored["future_option"] == {"enabled": True}
    assert stored["extension"] == [1, 2]


@pytest.mark.parametrize(("name", "loader", "saver", "factory"), CONFIG_CASES)
def test_explicit_save_preserves_unknown_top_level_fields(
    tmp_path: Path,
    name: str,
    loader: Loader,
    saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    initial = {"schema_version": 1, **asdict(factory()), "future_option": "keep-me"}
    path.write_text(json.dumps(initial), encoding="utf-8")
    loader(path)
    changed = factory()
    if isinstance(changed, HostConfig):
        changed.signal_target = 9
    else:
        changed.volume = 0.75

    saver(changed, path)

    assert _read(path)["future_option"] == "keep-me"
    assert _read(_backup(path)) == _read(path)


@pytest.mark.parametrize(("name", "loader", "_saver", "factory"), CONFIG_CASES)
def test_second_load_of_canonical_file_does_not_change_content(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(asdict(factory())), encoding="utf-8")
    loader(path)
    first_primary = path.read_bytes()
    first_backup = _backup(path).read_bytes()

    loader(path)

    assert path.read_bytes() == first_primary
    assert _backup(path).read_bytes() == first_backup


@pytest.mark.parametrize(("name", "loader", "_saver", "factory"), CONFIG_CASES)
def test_explicit_legacy_version_zero_is_migrated(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps({"schema_version": 0, **asdict(factory())}), encoding="utf-8")

    loader(path)

    assert _read(path)["schema_version"] == SCHEMA_VERSION


@pytest.mark.parametrize("version", [True, False, -1, "1", 1.0, None, []])
@pytest.mark.parametrize(("name", "loader", "_saver", "factory"), CONFIG_CASES)
def test_invalid_schema_versions_are_rejected_without_overwrite(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    factory: Callable[[], Config],
    version: object,
) -> None:
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps({"schema_version": version, **asdict(factory())}), encoding="utf-8")
    before = path.read_bytes()

    with pytest.raises(InvalidConfigVersionError):
        loader(path)

    assert path.read_bytes() == before
    assert not _backup(path).exists()


@pytest.mark.parametrize(("name", "loader", "_saver", "factory"), CONFIG_CASES)
def test_future_version_rejects_without_backup_fallback_or_overwrite(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    future = {"schema_version": 2, **asdict(factory()), "new_data": "must-survive"}
    current = {"schema_version": 1, **asdict(factory())}
    path.write_text(json.dumps(future), encoding="utf-8")
    _backup(path).write_text(json.dumps(current), encoding="utf-8")
    before_primary = path.read_bytes()
    before_backup = _backup(path).read_bytes()

    with pytest.raises(UnsupportedConfigVersionError):
        loader(path)

    assert path.read_bytes() == before_primary
    assert _backup(path).read_bytes() == before_backup


@pytest.mark.parametrize(("name", "loader", "saver", "factory"), CONFIG_CASES)
def test_corrupt_primary_is_preserved_and_recovered_from_valid_backup(
    tmp_path: Path,
    name: str,
    loader: Loader,
    saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    expected = factory()
    saver(expected, path)
    corrupt_bytes = b'{"schema_version": 1, broken'
    path.write_bytes(corrupt_bytes)

    assert loader(path) == expected

    corrupt_files = list(tmp_path.glob(f"{name}.json.*.corrupt"))
    assert len(corrupt_files) == 1
    assert corrupt_files[0].read_bytes() == corrupt_bytes
    assert _read(path) == _read(_backup(path))


@pytest.mark.parametrize(("name", "loader", "_saver", "_factory"), CONFIG_CASES)
def test_corrupt_primary_without_backup_raises_without_default_reset(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    _factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    corrupt_bytes = b"not-json"
    path.write_bytes(corrupt_bytes)

    with pytest.raises(ConfigRecoveryError):
        loader(path)

    assert path.read_bytes() == corrupt_bytes
    assert not list(tmp_path.glob(f"{name}.json.*.corrupt"))


@pytest.mark.parametrize(("name", "loader", "_saver", "_factory"), CONFIG_CASES)
def test_corrupt_backup_is_not_accepted_for_recovery(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    _factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    path.write_text("[]", encoding="utf-8")
    _backup(path).write_text("also broken", encoding="utf-8")
    before_primary = path.read_bytes()
    before_backup = _backup(path).read_bytes()

    with pytest.raises(ConfigRecoveryError):
        loader(path)

    assert path.read_bytes() == before_primary
    assert _backup(path).read_bytes() == before_backup


@pytest.mark.parametrize(("name", "_loader", "saver", "factory"), CONFIG_CASES)
def test_replace_failure_preserves_primary_and_removes_temporary_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    _loader: Loader,
    saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    original = factory()
    saver(original, path)
    original_bytes = path.read_bytes()
    changed = factory()
    if isinstance(changed, HostConfig):
        changed.tcp_port += 1
    else:
        changed.volume = 0.8
    real_replace = os.replace

    def fail_primary_replace(
        source: str | bytes | os.PathLike[str], target: str | bytes | os.PathLike[str]
    ) -> None:
        if Path(target) == path:
            raise OSError("simulated replace failure")
        real_replace(source, target)

    monkeypatch.setattr(config_module.os, "replace", fail_primary_replace)

    with pytest.raises(ConfigWriteError):
        saver(changed, path)

    assert path.read_bytes() == original_bytes
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob(".*.tmp"))
    json.loads(_backup(path).read_text(encoding="utf-8"))


@pytest.mark.parametrize(("name", "_loader", "saver", "factory"), CONFIG_CASES)
def test_fsync_failure_preserves_primary_and_backup_and_removes_temporary_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    _loader: Loader,
    saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    saver(factory(), path)
    original_primary = path.read_bytes()
    original_backup = _backup(path).read_bytes()

    def fail_fsync(_descriptor: int) -> None:
        raise OSError("simulated fsync failure")

    monkeypatch.setattr(config_module.os, "fsync", fail_fsync)

    with pytest.raises(ConfigWriteError):
        saver(factory(), path)

    assert path.read_bytes() == original_primary
    assert _backup(path).read_bytes() == original_backup
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.parametrize(("name", "loader", "saver", "factory"), CONFIG_CASES)
def test_backup_is_complete_valid_json_after_every_successful_save(
    tmp_path: Path,
    name: str,
    loader: Loader,
    saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    first = factory()
    saver(first, path)
    second = loader(path)
    if isinstance(second, HostConfig):
        second.window_seconds = 7.25
    else:
        second.output_device_id = 11

    saver(second, path)

    assert _read(_backup(path)) == {"schema_version": SCHEMA_VERSION, **asdict(second)}
    assert _backup(path).read_bytes().endswith(b"\n")


@pytest.mark.parametrize(("name", "loader", "_saver", "factory"), CONFIG_CASES)
def test_current_file_with_missing_known_fields_is_canonicalized(
    tmp_path: Path,
    name: str,
    loader: Loader,
    _saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    partial = {"schema_version": 1, "unknown": 42}
    if name == "host":
        partial["psk"] = "EXISTING"
    path.write_text(json.dumps(partial), encoding="utf-8")

    loaded = loader(path)

    assert _read(path) == {"schema_version": 1, **asdict(loaded), "unknown": 42}
    assert _read(_backup(path)) == _read(path)


@pytest.mark.parametrize(("name", "loader", "saver", "factory"), CONFIG_CASES)
def test_missing_primary_is_restored_from_backup(
    tmp_path: Path,
    name: str,
    loader: Loader,
    saver: Saver,
    factory: Callable[[], Config],
) -> None:
    path = tmp_path / f"{name}.json"
    expected = factory()
    saver(expected, path)
    path.unlink()

    assert loader(path) == expected
    assert _read(path) == _read(_backup(path))
