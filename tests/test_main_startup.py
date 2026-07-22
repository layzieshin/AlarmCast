"""Tests for CLI / frozen startup mode resolution."""

from __future__ import annotations

from pathlib import Path

from alarmcast import __main__ as entry


def test_resolve_startup_mode_from_argv() -> None:
    assert entry._resolve_startup_mode(["--host"]) == "host"
    assert entry._resolve_startup_mode(["--client"]) == "client"


def test_read_and_save_mode_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(entry, "_mode_file_path", lambda: tmp_path / "mode.txt")
    entry._save_mode("host")
    assert entry._read_saved_mode() == "host"
    entry._save_mode("client")
    assert entry._read_saved_mode() == "client"


def test_main_dispatches_host(monkeypatch) -> None:
    monkeypatch.setattr(entry, "run_host_mode", lambda: 11)
    monkeypatch.setattr(entry, "_ensure_single_instance", lambda _arg_list: None)
    assert entry.main(["--host"]) == 11


def test_main_dispatches_client(monkeypatch) -> None:
    monkeypatch.setattr(entry, "run_client_mode", lambda: 22)
    monkeypatch.setattr(entry, "_ensure_single_instance", lambda _arg_list: None)
    assert entry.main(["--client"]) == 22
