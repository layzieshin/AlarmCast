"""Windows registry autostart helpers for Host and Client modes."""

from __future__ import annotations

import logging
import sys

LOGGER = logging.getLogger(__name__)

_AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REGISTRY_NAMES = {
    "host": "AlarmcastHost",
    "client": "AlarmcastClient",
}


def set_windows_autostart(mode: str, enabled: bool) -> None:
    """Enable or disable login autostart for the given Alarmcast mode."""
    if sys.platform != "win32":
        return
    if mode not in _REGISTRY_NAMES:
        raise ValueError(f"Unknown mode: {mode}")

    import winreg

    name = _REGISTRY_NAMES[mode]
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        _AUTOSTART_KEY,
        0,
        winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
    )
    try:
        if enabled:
            exe = sys.executable
            flag = f"--{mode}"
            if getattr(sys, "frozen", False):
                cmd = f'"{exe}" {flag}'
            else:
                cmd = f'"{exe}" -m alarmcast {flag}'
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, cmd)
            LOGGER.info("Autostart enabled [mode=%s]", mode)
        else:
            try:
                winreg.DeleteValue(key, name)
                LOGGER.info("Autostart disabled [mode=%s]", mode)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)
