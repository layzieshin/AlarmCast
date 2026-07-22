"""PyInstaller runtime hook: multiprocessing + Qt plugin path when frozen."""

from __future__ import annotations

import multiprocessing
import os
import sys

multiprocessing.freeze_support()

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    base = getattr(sys, "_MEIPASS")
    plugins = os.path.join(base, "PySide6", "plugins")
    if os.path.isdir(plugins):
        os.environ["QT_PLUGIN_PATH"] = plugins
    platforms = os.path.join(plugins, "platforms")
    if os.path.isdir(platforms):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms
