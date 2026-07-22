# -*- mode: python ; coding: utf-8 -*-
"""Debug build: same as alarmcast.spec but with console=True (errors visible in terminal)."""

from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas: list = []
binaries: list = []
hiddenimports: list = [
    "alarmcast",
    "alarmcast.core",
    "alarmcast.core.alarm_logic",
    "alarmcast.core.audio_format",
    "alarmcast.core.autostart",
    "alarmcast.core.config",
    "alarmcast.core.discovery",
    "alarmcast.core.event_log",
    "alarmcast.core.logging_setup",
    "alarmcast.core.mode_switch",
    "alarmcast.core.protocol",
    "alarmcast.core.security",
    "alarmcast.core.single_instance",
    "alarmcast.core.ui_theme",
    "alarmcast.host",
    "alarmcast.host.app",
    "alarmcast.host.capture",
    "alarmcast.host.detector",
    "alarmcast.host.server",
    "alarmcast.host.ui",
    "alarmcast.host.ui.main_window",
    "alarmcast.client",
    "alarmcast.client.app",
    "alarmcast.client.net",
    "alarmcast.client.output",
    "alarmcast.client.overlay",
    "alarmcast.client.message_overlay",
    "alarmcast.client.ui",
    "alarmcast.client.ui.main_window",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    "_overlapped",
    "asyncio.windows_events",
    "asyncio.windows_utils",
    "numpy",
    "sounddevice",
    "soundcard",
    "zeroconf",
    "ifaddr",
]

for pkg in ("soundcard", "sounddevice", "zeroconf"):
    tmp = collect_all(pkg)
    datas += tmp[0]
    binaries += tmp[1]
    hiddenimports += tmp[2]

excludes = [
    "tkinter",
    "matplotlib",
    "pandas",
    "scipy",
    "PIL",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickControls2",
    "PySide6.QtWebEngine",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtSql",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtMultimedia",
    "PySide6.QtNetworkAuth",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtLocation",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtTest",
    "PySide6.QtUiTools",
]

a = Analysis(
    ["src/alarmcast/__main__.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["hooks/pyi_rth_alarmcast.py"],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="alarmcast-debug",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
