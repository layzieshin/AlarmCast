"""Persisted Host/Client mode and process relaunch."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from alarmcast.core.config import get_config_dir

MODE_FILE_NAME = "mode.txt"


def mode_file_path() -> Path:
    """Return path to the saved application mode file."""
    return get_config_dir() / MODE_FILE_NAME


def read_saved_mode() -> str | None:
    """Return 'host', 'client', or None if unset/invalid."""
    path = mode_file_path()
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip().lower()
    if text in ("host", "client"):
        return text
    return None


def save_mode(mode: str) -> None:
    """Write the selected mode for the next application start."""
    if mode not in ("host", "client"):
        raise ValueError(f"Invalid mode: {mode}")
    path = mode_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(mode, encoding="utf-8")


def relaunch_as_mode(mode: str) -> bool:
    """Start a new Alarmcast process in the given mode. Returns False on failure."""
    if mode not in ("host", "client"):
        return False
    save_mode(mode)

    from PySide6.QtCore import QProcess, QProcessEnvironment

    exe = sys.executable
    if getattr(sys, "frozen", False):
        args = [f"--{mode}"]
    else:
        args = ["-m", "alarmcast", f"--{mode}"]

    process = QProcess()
    process.setProgram(exe)
    process.setArguments(args)

    env = QProcessEnvironment()
    for key, value in os.environ.items():
        # Prevent inherited one-file bootloader and stale Qt plugin state
        # from breaking mode switches in frozen builds.
        if key in {
            "_MEIPASS2",
            "_PYI_APPLICATION_HOME_DIR",
            "_PYI_ARCHIVE_FILE",
            "_PYI_PARENT_PROCESS_LEVEL",
            "_PYI_SPLASH_IPC",
            "QT_PLUGIN_PATH",
            "QT_QPA_PLATFORM_PLUGIN_PATH",
        }:
            continue
        env.insert(key, value)
    env.insert("PYINSTALLER_RESET_ENVIRONMENT", "1")
    process.setProcessEnvironment(env)

    return bool(process.startDetached())
