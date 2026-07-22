"""Smoke tests for the phase-2 entrypoint."""

from __future__ import annotations

from alarmcast import __main__


def test_main_dispatches_host(monkeypatch) -> None:
    """Host mode delegates to the host app runner."""

    def fake_host_run_mode() -> int:
        return 11

    monkeypatch.setattr(__main__, "run_host_mode", fake_host_run_mode)
    monkeypatch.setattr(
        __main__,
        "_ensure_single_instance",
        lambda _arg_list: None,
    )
    assert __main__.main(["--host"]) == 11


def test_main_dispatches_client(monkeypatch) -> None:
    """Client mode delegates to the client app runner."""

    def fake_client_run_mode() -> int:
        return 22

    monkeypatch.setattr(__main__, "run_client_mode", fake_client_run_mode)
    monkeypatch.setattr(
        __main__,
        "_ensure_single_instance",
        lambda _arg_list: None,
    )
    assert __main__.main(["--client"]) == 22
