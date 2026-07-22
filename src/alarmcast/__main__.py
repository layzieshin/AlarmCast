"""CLI entrypoint for Alarmcast."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

MODE_FILE_NAME = "mode.txt"


def _prepare_frozen_runtime() -> None:
    import multiprocessing

    multiprocessing.freeze_support()


def _mode_file_path() -> Path:
    from alarmcast.core.config import get_config_dir

    return get_config_dir() / MODE_FILE_NAME


def _read_saved_mode() -> str | None:
    path = _mode_file_path()
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip().lower()
    if text in ("host", "client"):
        return text
    return None


def _save_mode(mode: str) -> None:
    path = _mode_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(mode, encoding="utf-8")


def _argv_has_mode(argv: Sequence[str]) -> bool:
    return "--host" in argv or "--client" in argv


def _pick_mode_dialog() -> str | None:
    """Show Host/Client picker when EXE is started without arguments."""
    from PySide6.QtWidgets import QApplication, QMessageBox

    _app = QApplication.instance() or QApplication(sys.argv)  # keep QApplication alive
    box = QMessageBox()
    box.setWindowTitle("Alarmcast")
    box.setText("Bitte Modus waehlen:")
    box.setInformativeText(
        "Host = PC am Analysengeraet\nClient = Arzt-PC\n\n"
        "Tipp: Verknuepfungen mit --host oder --client ueberspringen diesen Dialog."
    )
    host_btn = box.addButton("Host", QMessageBox.ButtonRole.AcceptRole)
    client_btn = box.addButton("Client", QMessageBox.ButtonRole.AcceptRole)
    box.addButton("Abbrechen", QMessageBox.ButtonRole.RejectRole)
    box.exec()
    clicked = box.clickedButton()
    if clicked == host_btn:
        return "host"
    if clicked == client_btn:
        return "client"
    return None


def _resolve_startup_mode(argv: Sequence[str]) -> str | None:
    """Return 'host' or 'client', or None if startup should abort."""
    if "--host" in argv:
        return "host"
    if "--client" in argv:
        return "client"

    if getattr(sys, "frozen", False):
        saved = _read_saved_mode()
        if saved is not None:
            return saved
        picked = _pick_mode_dialog()
        if picked is not None:
            _save_mode(picked)
        return picked

    return None


def build_parser() -> argparse.ArgumentParser:
    """Create the Alarmcast argument parser (development CLI)."""
    parser = argparse.ArgumentParser(prog="alarmcast")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--host", action="store_true", help="run in host mode")
    mode_group.add_argument("--client", action="store_true", help="run in client mode")
    parser.add_argument(
        "--allow-multiple",
        action="store_true",
        help="allow more than one Alarmcast process (development only)",
    )
    return parser


def run_host_mode() -> int:
    """Import and run host mode lazily."""
    from alarmcast.host.app import run as run_host

    return run_host()


def run_client_mode() -> int:
    """Import and run client mode lazily."""
    from alarmcast.client.app import run as run_client

    return run_client()


def _should_allow_multiple(arg_list: Sequence[str]) -> bool:
    return "--allow-multiple" in arg_list


def _ensure_single_instance(arg_list: Sequence[str]) -> int | None:
    """Return exit code if this process should exit; None to continue startup."""
    from alarmcast.core.single_instance import notify_existing_instance

    if _should_allow_multiple(arg_list):
        return None
    if notify_existing_instance():
        return 0
    return None


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and dispatch to the selected mode."""
    _prepare_frozen_runtime()

    arg_list = list(argv) if argv is not None else sys.argv[1:]
    filtered_args = [a for a in arg_list if a != "--allow-multiple"]

    early_exit = _ensure_single_instance(arg_list)
    if early_exit is not None:
        return early_exit

    if not _argv_has_mode(arg_list):
        mode = _resolve_startup_mode(arg_list)
        if mode is None:
            if getattr(sys, "frozen", False):
                return 1
            build_parser().print_help()
            return 2
        if mode == "host":
            return run_host_mode()
        return run_client_mode()

    parser = build_parser()
    args = parser.parse_args(filtered_args)
    if args.host:
        return run_host_mode()
    return run_client_mode()


if __name__ == "__main__":
    raise SystemExit(main())
