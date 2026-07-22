"""Tests for host event log."""

from __future__ import annotations

from pathlib import Path

from alarmcast.core import event_log


def test_append_and_read_recent(tmp_path: Path, monkeypatch: object) -> None:
    path = tmp_path / "events.jsonl"
    monkeypatch.setattr(event_log, "events_path", lambda: path)

    event_log.append_event("client_connected", {"name": "PC1", "addr": "10.0.0.1:1"})
    event_log.append_event("alarm_on")

    entries = event_log.read_recent()
    assert len(entries) == 2
    assert entries[0]["type"] == "alarm_on"
    assert entries[1]["type"] == "client_connected"
    assert entries[1]["detail"]["name"] == "PC1"


def test_format_event_row() -> None:
    entry = {
        "ts": "2026-05-22T10:00:00+00:00",
        "type": "reset_remote",
        "detail": {"client": "Backoffice2"},
    }
    ts, label, details = event_log.format_event_row(entry)
    assert "Reset" in label
    assert "Backoffice2" in details
