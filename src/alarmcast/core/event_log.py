"""Append-only host event log (JSONL) in %APPDATA%\\AlarmCast."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alarmcast.core.config import get_config_dir

EVENTS_FILE_NAME = "events.jsonl"
MAX_READ_ENTRIES = 500

EVENT_LABELS: dict[str, str] = {
    "client_connected": "Client verbunden",
    "client_disconnected": "Client getrennt",
    "alarm_on": "Alarm ausgeloest",
    "alarm_off": "Alarm beendet",
    "reset_local": "Reset (Host)",
    "reset_remote": "Reset (Client)",
    "message_sent": "Nachricht gesendet",
    "runtime_started": "Server gestartet",
    "runtime_stopped": "Server gestoppt",
}


def events_path() -> Path:
    """Return path to the host events JSONL file."""
    return get_config_dir() / EVENTS_FILE_NAME


def append_event(event_type: str, detail: dict[str, Any] | None = None) -> None:
    """Append one event line to the host event log."""
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "type": event_type,
        "detail": detail or {},
    }
    path = events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_recent(limit: int = MAX_READ_ENTRIES) -> list[dict[str, Any]]:
    """Read the most recent events (newest first)."""
    path = events_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[dict[str, Any]] = []
    for line in reversed(lines[-limit:]):
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(raw, dict):
            entries.append(raw)
    return entries


def format_event_row(entry: dict[str, Any]) -> tuple[str, str, str]:
    """Return (timestamp_local, label, details) for UI display."""
    ts_raw = str(entry.get("ts", ""))
    ts_display = _format_timestamp(ts_raw)
    event_type = str(entry.get("type", ""))
    label = EVENT_LABELS.get(event_type, event_type)
    detail = entry.get("detail")
    if not isinstance(detail, dict):
        detail = {}
    details = _format_detail(detail)
    return ts_display, label, details


def _format_timestamp(iso_ts: str) -> str:
    if not iso_ts:
        return ""
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        local = dt.astimezone()
        return local.strftime("%d.%m.%Y %H:%M:%S")
    except ValueError:
        return iso_ts


def _format_detail(detail: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("client", "name", "addr", "text", "port"):
        if key in detail and detail[key]:
            if key == "name":
                parts.append(str(detail[key]))
            elif key == "client":
                parts.append(str(detail[key]))
            elif key == "addr":
                parts.append(str(detail[key]))
            elif key == "text":
                parts.append(str(detail[key]))
            elif key == "port":
                parts.append(f"Port {detail[key]}")
    if not parts:
        return ""
    return " · ".join(parts)
