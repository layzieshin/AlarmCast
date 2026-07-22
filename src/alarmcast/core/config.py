r"""Versioned, atomic configuration I/O in %APPDATA%\AlarmCast."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from contextlib import suppress
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from alarmcast.core.protocol import TCP_PORT
from alarmcast.core.security import generate_psk

APP_NAME = "AlarmCast"
HOST_CONFIG_NAME = "host.json"
CLIENT_CONFIG_NAME = "client.json"
SCHEMA_VERSION = 1


class ConfigError(Exception):
    """Base class for configuration persistence failures."""


class ConfigLoadError(ConfigError):
    """A configuration file could not be loaded."""


class ConfigVersionError(ConfigLoadError):
    """A configuration schema version is invalid or unsupported."""


class InvalidConfigVersionError(ConfigVersionError):
    """The schema version value is not a supported non-negative integer."""


class UnsupportedConfigVersionError(ConfigVersionError):
    """The configuration was written by a newer application version."""


class ConfigRecoveryError(ConfigLoadError):
    """A broken or missing primary configuration could not be recovered."""


class ConfigWriteError(ConfigError):
    """A configuration file could not be written atomically."""


class _CorruptConfigData(Exception):
    """Internal marker for syntactically unusable configuration data."""


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
    """Load, migrate, or recover the host configuration."""
    path = _load_path(HOST_CONFIG_NAME, path_override)
    if not path.exists() and not _backup_path(path).exists():
        cfg = HostConfig(psk=generate_psk())
        _write_config(path, cfg, {})
        return cfg

    raw = _load_primary_document(path)
    cfg = _host_config_from(raw)
    _canonicalize_loaded_config(path, raw, cfg)
    return cfg


def save_host_config(cfg: HostConfig, path_override: Path | None = None) -> Path:
    """Persist host config atomically while retaining unknown top-level fields."""
    path = _write_path(HOST_CONFIG_NAME, path_override)
    unknown = _unknown_fields_for_save(path, HostConfig)
    _write_config(path, cfg, unknown)
    return path


def load_client_config(path_override: Path | None = None) -> ClientConfig:
    """Load, migrate, or recover the client configuration."""
    path = _load_path(CLIENT_CONFIG_NAME, path_override)
    if not path.exists() and not _backup_path(path).exists():
        cfg = ClientConfig()
        _write_config(path, cfg, {})
        return cfg

    raw = _load_primary_document(path)
    cfg = _client_config_from(raw)
    _canonicalize_loaded_config(path, raw, cfg)
    return cfg


def save_client_config(cfg: ClientConfig, path_override: Path | None = None) -> Path:
    """Persist client config atomically while retaining unknown top-level fields."""
    path = _write_path(CLIENT_CONFIG_NAME, path_override)
    unknown = _unknown_fields_for_save(path, ClientConfig)
    _write_config(path, cfg, unknown)
    return path


def _load_path(name: str, path_override: Path | None) -> Path:
    if path_override is not None:
        return path_override
    try:
        return get_config_dir() / name
    except OSError as exc:
        raise ConfigLoadError(f"Cannot access configuration directory: {exc}") from exc


def _write_path(name: str, path_override: Path | None) -> Path:
    if path_override is not None:
        return path_override
    try:
        return get_config_dir() / name
    except OSError as exc:
        raise ConfigWriteError(f"Cannot access configuration directory: {exc}") from exc


def _host_config_from(raw: dict[str, object]) -> HostConfig:
    return HostConfig(
        psk=str(raw.get("psk") or generate_psk()),
        threshold_rms=_as_float(raw.get("threshold_rms"), 0.06),
        signal_target=_as_int(raw.get("signal_target"), 2),
        window_seconds=_as_float(raw.get("window_seconds"), 3.0),
        tcp_port=_as_int(raw.get("tcp_port"), TCP_PORT),
        autostart_with_windows=bool(raw.get("autostart_with_windows", True)),
        auto_start_runtime=bool(raw.get("auto_start_runtime", True)),
    )


def _client_config_from(raw: dict[str, object]) -> ClientConfig:
    return ClientConfig(
        host_addr=str(raw.get("host_addr", "")),
        psk=str(raw.get("psk", "")),
        volume=_as_float(raw.get("volume"), 0.9),
        muted=bool(raw.get("muted", False)),
        output_device_id=_as_int(raw.get("output_device_id"), -1),
        autostart_with_windows=bool(raw.get("autostart_with_windows", True)),
        auto_connect=bool(raw.get("auto_connect", True)),
        message_overlay_enabled=bool(raw.get("message_overlay_enabled", True)),
    )


def _canonicalize_loaded_config(
    path: Path, raw: dict[str, object], cfg: HostConfig | ClientConfig
) -> None:
    unknown = _unknown_fields(raw, type(cfg))
    canonical = _document_for(cfg, unknown)
    if raw != canonical:
        _write_document_pair(path, canonical)
        return
    _ensure_current_backup(path, canonical)


def _unknown_fields_for_save(
    path: Path, config_type: type[HostConfig] | type[ClientConfig]
) -> dict[str, object]:
    if not path.exists() and not _backup_path(path).exists():
        return {}
    raw = _load_primary_document(path)
    return _unknown_fields(raw, config_type)


def _unknown_fields(
    raw: dict[str, object], config_type: type[HostConfig] | type[ClientConfig]
) -> dict[str, object]:
    known = {field.name for field in fields(config_type)}
    return {key: value for key, value in raw.items() if key not in known | {"schema_version"}}


def _write_config(path: Path, cfg: HostConfig | ClientConfig, unknown: dict[str, object]) -> None:
    _write_document_pair(path, _document_for(cfg, unknown))


def _document_for(cfg: HostConfig | ClientConfig, unknown: dict[str, object]) -> dict[str, object]:
    document: dict[str, object] = {"schema_version": SCHEMA_VERSION}
    document.update(asdict(cfg))
    document.update(unknown)
    return document


def _load_primary_document(path: Path) -> dict[str, object]:
    if not path.exists():
        return _recover_missing_primary(path)
    try:
        document = _read_json_object(path)
    except _CorruptConfigData:
        return _recover_corrupt_primary(path)
    _schema_version(document, path)
    return document


def _recover_missing_primary(path: Path) -> dict[str, object]:
    backup = _read_valid_backup(path)
    try:
        _atomic_write_json(path, backup)
    except ConfigWriteError as exc:
        raise ConfigRecoveryError(
            f"Cannot restore missing configuration {path} from its backup"
        ) from exc
    return backup


def _recover_corrupt_primary(path: Path) -> dict[str, object]:
    backup = _read_valid_backup(path)
    corrupt_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.corrupt")
    try:
        broken_bytes = path.read_bytes()
        _atomic_write_bytes(corrupt_path, broken_bytes)
        _atomic_write_json(path, backup)
    except (OSError, ConfigWriteError) as exc:
        raise ConfigRecoveryError(
            f"Cannot preserve and recover corrupt configuration {path}"
        ) from exc
    return backup


def _read_valid_backup(path: Path) -> dict[str, object]:
    backup_path = _backup_path(path)
    if not backup_path.exists():
        raise ConfigRecoveryError(f"No valid backup exists for configuration {path}")
    try:
        backup = _read_json_object(backup_path)
        _schema_version(backup, backup_path)
    except (ConfigLoadError, ConfigVersionError, _CorruptConfigData) as exc:
        raise ConfigRecoveryError(f"Backup configuration is not valid: {backup_path}") from exc
    return backup


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh, parse_constant=_reject_non_json_constant)
    except (ValueError, UnicodeDecodeError) as exc:
        raise _CorruptConfigData(f"Configuration is not valid JSON: {path}") from exc
    except OSError as exc:
        raise ConfigLoadError(f"Cannot read configuration {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise _CorruptConfigData(f"Configuration is not a JSON object: {path}")
    return data


def _schema_version(data: dict[str, object], path: Path) -> int:
    version = data.get("schema_version", 0)
    if isinstance(version, bool) or not isinstance(version, int) or version < 0:
        raise InvalidConfigVersionError(f"Invalid schema_version in configuration {path}")
    if version > SCHEMA_VERSION:
        raise UnsupportedConfigVersionError(
            f"Unsupported schema_version {version} in configuration {path}"
        )
    return version


def _reject_non_json_constant(value: str) -> object:
    raise ValueError(f"Non-JSON numeric constant: {value}")


def _ensure_current_backup(path: Path, document: dict[str, object]) -> None:
    backup_path = _backup_path(path)
    if backup_path.exists():
        try:
            backup = _read_json_object(backup_path)
            _schema_version(backup, backup_path)
        except UnsupportedConfigVersionError:
            raise
        except (ConfigLoadError, ConfigVersionError, _CorruptConfigData):
            backup = None
        if backup == document:
            return
    _atomic_write_json(backup_path, document)


def _write_document_pair(path: Path, document: dict[str, object]) -> None:
    _atomic_write_json(_backup_path(path), document)
    _atomic_write_json(path, document)


def _backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.bak")


def _atomic_write_json(path: Path, data: dict[str, object]) -> None:
    try:
        payload = json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    except (TypeError, ValueError) as exc:
        raise ConfigWriteError(f"Configuration cannot be serialized for {path}") from exc
    _atomic_write_bytes(path, payload.encode("utf-8"))


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    temp_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )
        temp_path = Path(temp_name)
        with os.fdopen(descriptor, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, path)
        temp_path = None
    except OSError as exc:
        raise ConfigWriteError(f"Cannot atomically write configuration {path}: {exc}") from exc
    finally:
        if temp_path is not None:
            with suppress(OSError):
                temp_path.unlink()


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
