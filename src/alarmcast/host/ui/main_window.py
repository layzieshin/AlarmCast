"""Host mode main window with tabbed UI."""

from __future__ import annotations

import logging
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from alarmcast.core.autostart import set_windows_autostart
from alarmcast.core.config import HostConfig, get_config_dir, load_host_config, save_host_config
from alarmcast.core.discovery import PublishedService, publish_host
from alarmcast.core.event_log import append_event, events_path, format_event_row, read_recent
from alarmcast.core.mode_switch import read_saved_mode, relaunch_as_mode, save_mode
from alarmcast.core.protocol import ALM_OFF, ALM_ON, MessageMode, encode_message
from alarmcast.host.capture import LoopbackCapture
from alarmcast.host.detector import HostDetector
from alarmcast.host.server import HostServer

LOGGER = logging.getLogger(__name__)

_HOST_WINDOW_W = 480
_HOST_WINDOW_H = 520
_CONTENT_MARGINS = 10
_LIST_MAX_HEIGHT = 120

_STATUS_COLORS = {
    "idle": "#9e9e9e",
    "running": "#43a047",
    "alarm": "#f9a825",
}


class _HostSignals(QObject):
    remote_reset_requested = Signal(str)
    alarm_active_changed = Signal(bool)


class _HostRuntime:
    """Runtime wiring for server, discovery, detector and capture."""

    def __init__(
        self,
        on_remote_reset: Callable[[str], None],
        on_alarm_active: Callable[[bool], None],
    ) -> None:
        self._on_remote_reset = on_remote_reset
        self._on_alarm_active = on_alarm_active
        self._lock = threading.Lock()
        self._server: HostServer | None = None
        self._capture: LoopbackCapture | None = None
        self._detector: HostDetector | None = None
        self._published_service: PublishedService | None = None
        self._alarm_active = False

    @property
    def running(self) -> bool:
        with self._lock:
            return self._server is not None and self._server.running

    @property
    def alarm_active(self) -> bool:
        return self._alarm_active

    def start(self, cfg: HostConfig) -> None:
        with self._lock:
            if self._server is not None:
                return

            server = HostServer(
                port=cfg.tcp_port,
                expected_psk=cfg.psk,
                on_reset_request=self._on_remote_reset,
            )
            server.start()

            published = publish_host(cfg.tcp_port)

            def on_alarm_on() -> None:
                self._alarm_active = True
                append_event("alarm_on")
                self._on_alarm_active(True)
                server.broadcast_control(ALM_ON)

            def on_alarm_off() -> None:
                self._alarm_active = False
                append_event("alarm_off")
                self._on_alarm_active(False)
                server.broadcast_control(ALM_OFF)

            detector = HostDetector(
                threshold_rms=cfg.threshold_rms,
                signal_target=cfg.signal_target,
                window_seconds=cfg.window_seconds,
                on_alarm_on=on_alarm_on,
                on_alarm_off=on_alarm_off,
            )
            capture = LoopbackCapture(
                on_frame=lambda payload: self._on_audio_frame(server, detector, payload)
            )
            capture.start()

            self._server = server
            self._capture = capture
            self._detector = detector
            self._published_service = published

        append_event("runtime_started", {"port": cfg.tcp_port})

    def stop(self, tcp_port: int = 0) -> None:
        with self._lock:
            capture = self._capture
            server = self._server
            published = self._published_service
            self._capture = None
            self._detector = None
            self._server = None
            self._published_service = None
            self._alarm_active = False

        if capture is not None:
            capture.stop()
        if published is not None:
            published.close()
        if server is not None:
            server.stop()

        append_event("runtime_stopped", {"port": tcp_port} if tcp_port else {})
        self._on_alarm_active(False)

    def reset_alarm(self) -> None:
        with self._lock:
            detector = self._detector
            server = self._server
        if detector is not None:
            detector.reset()
        if server is not None:
            server.broadcast_control(ALM_OFF)

    def broadcast_message(self, text: str, mode: MessageMode = "status") -> None:
        with self._lock:
            server = self._server
        if server is None:
            return
        payload = encode_message(text, mode=mode)
        server.broadcast_control(payload)
        append_event("message_sent", {"text": text[:200], "mode": mode})

    def clients(self) -> list[str]:
        with self._lock:
            server = self._server
        return server.get_clients_snapshot() if server is not None else []

    @staticmethod
    def _on_audio_frame(server: HostServer, detector: HostDetector, payload: bytes) -> None:
        server.broadcast_audio(payload)
        detector.process_audio_payload(payload)


class HostWindow(QMainWindow):
    """Host settings and runtime controls."""

    def __init__(self) -> None:
        super().__init__()
        self._signals = _HostSignals()
        self._signals.remote_reset_requested.connect(self._handle_remote_reset)
        self._signals.alarm_active_changed.connect(self._on_alarm_active_changed)
        self._runtime = _HostRuntime(
            on_remote_reset=self._signals.remote_reset_requested.emit,
            on_alarm_active=self._signals.alarm_active_changed.emit,
        )

        self._cfg = load_host_config()
        self._tray_icon: QSystemTrayIcon | None = None
        self._status_mode = "idle"
        self._mode_switching = False
        self._tray_hint_shown = False

        self.setWindowTitle("Alarmcast Host")
        self.setFixedSize(_HOST_WINDOW_W, _HOST_WINDOW_H)
        self._build_ui()
        self._load_config_into_controls()
        self._setup_tray()
        self._update_status_display("Bereit", "idle")
        self._update_reset_visibility()

        self._client_timer = QTimer(self)
        self._client_timer.setInterval(1000)
        self._client_timer.timeout.connect(self._refresh_clients)
        self._client_timer.start()

        self._event_timer = QTimer(self)
        self._event_timer.setInterval(1000)
        self._event_timer.timeout.connect(self._refresh_event_log)
        self._event_timer.start()
        self._refresh_event_log()

        if self._cfg.autostart_with_windows:
            try:
                set_windows_autostart("host", True)
            except OSError as exc:
                LOGGER.warning("Host autostart konnte nicht gesetzt werden: %s", exc)

        if self._cfg.auto_start_runtime:
            QTimer.singleShot(0, self._start_runtime)

    def _build_ui(self) -> None:
        tabs = QTabWidget(self)
        self.setCentralWidget(tabs)
        m = _CONTENT_MARGINS

        overview = QWidget()
        overview_layout = QVBoxLayout(overview)
        overview_layout.setContentsMargins(m, m, m, m)
        overview_layout.setSpacing(8)

        self._status_card = QFrame()
        self._status_card.setObjectName("statusCard")
        status_layout = QHBoxLayout(self._status_card)
        self._status_dot = QLabel()
        self._status_dot.setObjectName("statusDot")
        self._status_title = QLabel("Bereit")
        self._status_title.setObjectName("statusTitle")
        status_layout.addWidget(self._status_dot)
        status_layout.addWidget(self._status_title, stretch=1)
        overview_layout.addWidget(self._status_card)

        overview_layout.addWidget(QLabel("Verbundene Clients"))
        self.clients_list = QListWidget()
        self.clients_list.setMaximumHeight(_LIST_MAX_HEIGHT)
        overview_layout.addWidget(self.clients_list)

        msg_row = QHBoxLayout()
        self.message_mode_combo = QComboBox()
        self.message_mode_combo.addItems(["Nur Status", "Info (10s)", "Bestaetigung"])
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Nachricht an alle Clients")
        self.message_edit.setMaxLength(200)
        self.send_message_button = QPushButton("Senden")
        self.send_message_button.setEnabled(False)
        self.send_message_button.clicked.connect(self._send_broadcast_message)
        msg_row.addWidget(self.message_mode_combo)
        msg_row.addWidget(self.message_edit, stretch=1)
        msg_row.addWidget(self.send_message_button)
        overview_layout.addLayout(msg_row)

        self._last_message_label = QLabel("")
        self._last_message_label.setWordWrap(True)
        self._last_message_label.setStyleSheet("color: #5c6570; font-size: 9pt;")
        overview_layout.addWidget(self._last_message_label)

        btn_row = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self._start_runtime)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_runtime)
        self.stop_button.setEnabled(False)
        self.reset_button = QPushButton("Alarm zuruecksetzen")
        self.reset_button.setObjectName("primaryButton")
        self.reset_button.clicked.connect(self._reset_alarm)
        btn_row.addWidget(self.start_button)
        btn_row.addWidget(self.stop_button)
        btn_row.addWidget(self.reset_button)
        overview_layout.addLayout(btn_row)
        overview_layout.addStretch()

        tabs.addTab(overview, "Uebersicht")

        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        settings_widget = QWidget()
        settings_layout = QGridLayout(settings_widget)
        settings_layout.setContentsMargins(m, m, m, m)
        settings_layout.setVerticalSpacing(8)

        row = 0
        settings_layout.addWidget(QLabel("Rolle"), row, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Host", "Client"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_combo_changed)
        settings_layout.addWidget(self.mode_combo, row, 1)
        row += 1

        self.autostart_check = QCheckBox("Mit Windows starten")
        settings_layout.addWidget(self.autostart_check, row, 0, 1, 2)
        row += 1

        self.auto_start_check = QCheckBox("Server beim App-Start automatisch starten")
        settings_layout.addWidget(self.auto_start_check, row, 0, 1, 2)
        row += 1

        settings_layout.addWidget(QLabel("RMS-Schwelle"), row, 0)
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.001, 1.0)
        self.threshold_spin.setDecimals(3)
        self.threshold_spin.setSingleStep(0.005)
        settings_layout.addWidget(self.threshold_spin, row, 1)
        row += 1

        settings_layout.addWidget(QLabel("Signale im Fenster"), row, 0)
        self.signal_count_spin = QSpinBox()
        self.signal_count_spin.setRange(1, 10)
        settings_layout.addWidget(self.signal_count_spin, row, 1)
        row += 1

        settings_layout.addWidget(QLabel("Fenster (Sekunden)"), row, 0)
        self.window_seconds_spin = QDoubleSpinBox()
        self.window_seconds_spin.setRange(0.5, 20.0)
        self.window_seconds_spin.setDecimals(1)
        self.window_seconds_spin.setSingleStep(0.5)
        settings_layout.addWidget(self.window_seconds_spin, row, 1)
        row += 1

        settings_layout.addWidget(QLabel("TCP-Port"), row, 0)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        settings_layout.addWidget(self.port_spin, row, 1)
        row += 1

        settings_layout.addWidget(QLabel("PSK"), row, 0)
        psk_row = QHBoxLayout()
        self.psk_value_label = QLabel("")
        self.psk_value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        psk_row.addWidget(self.psk_value_label, stretch=1)
        copy_psk_btn = QPushButton("Kopieren")
        copy_psk_btn.clicked.connect(self._copy_psk)
        psk_row.addWidget(copy_psk_btn)
        settings_layout.addLayout(psk_row, row, 1)
        row += 1

        self.save_settings_button = QPushButton("Speichern")
        self.save_settings_button.setObjectName("primaryButton")
        self.save_settings_button.clicked.connect(self._on_save_settings_clicked)
        settings_layout.addWidget(self.save_settings_button, row, 0, 1, 2)
        row += 1

        self._settings_saved_label = QLabel("")
        self._settings_saved_label.setStyleSheet("color: #43a047; font-size: 9pt;")
        settings_layout.addWidget(self._settings_saved_label, row, 0, 1, 2)

        settings_scroll.setWidget(settings_widget)
        tabs.addTab(settings_scroll, "Einstellungen")

        logs = QWidget()
        logs_layout = QVBoxLayout(logs)
        logs_layout.setContentsMargins(m, m, m, m)

        self.event_table = QTableWidget(0, 3)
        self.event_table.setHorizontalHeaderLabels(["Zeit", "Ereignis", "Details"])
        self.event_table.horizontalHeader().setStretchLastSection(True)
        self.event_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.event_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        logs_layout.addWidget(self.event_table)

        logs_btn_row = QHBoxLayout()
        self.open_events_button = QPushButton("Ereignislog oeffnen")
        self.open_events_button.clicked.connect(self._open_events_log)
        self.open_runtime_log_button = QPushButton("Technisches Log oeffnen")
        self.open_runtime_log_button.clicked.connect(self._open_runtime_log)
        logs_btn_row.addWidget(self.open_events_button)
        logs_btn_row.addWidget(self.open_runtime_log_button)
        logs_btn_row.addStretch()
        logs_layout.addLayout(logs_btn_row)

        tabs.addTab(logs, "Logs")

    def _load_config_into_controls(self) -> None:
        self._mode_switching = True
        saved = read_saved_mode() or "host"
        self.mode_combo.setCurrentIndex(0 if saved == "host" else 1)
        self._mode_switching = False

        self.autostart_check.setChecked(self._cfg.autostart_with_windows)
        self.auto_start_check.setChecked(self._cfg.auto_start_runtime)
        self.threshold_spin.setValue(self._cfg.threshold_rms)
        self.signal_count_spin.setValue(self._cfg.signal_target)
        self.window_seconds_spin.setValue(self._cfg.window_seconds)
        self.port_spin.setValue(self._cfg.tcp_port)
        self.psk_value_label.setText(self._cfg.psk)

    def _on_save_settings_clicked(self) -> None:
        self._save_controls_to_config()
        self._settings_saved_label.setText("Einstellungen gespeichert.")
        QTimer.singleShot(4000, self._settings_saved_label.clear)

    def _save_controls_to_config(self) -> None:
        self._cfg.threshold_rms = float(self.threshold_spin.value())
        self._cfg.signal_target = int(self.signal_count_spin.value())
        self._cfg.window_seconds = float(self.window_seconds_spin.value())
        self._cfg.tcp_port = int(self.port_spin.value())
        self._cfg.autostart_with_windows = self.autostart_check.isChecked()
        self._cfg.auto_start_runtime = self.auto_start_check.isChecked()
        save_host_config(self._cfg)
        try:
            set_windows_autostart("host", self._cfg.autostart_with_windows)
        except OSError as exc:
            LOGGER.warning("Host autostart update failed: %s", exc)

    def _on_mode_combo_changed(self, index: int) -> None:
        if self._mode_switching:
            return
        new_mode = "host" if index == 0 else "client"
        current = read_saved_mode() or "host"
        if new_mode == current:
            return

        reply = QMessageBox.question(
            self,
            "Rolle wechseln",
            f"Alarmcast wird als {'Host' if new_mode == 'host' else 'Client'} neu gestartet.\n"
            "Laufende Verbindungen werden beendet. Fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            self._mode_switching = True
            self.mode_combo.setCurrentIndex(0 if current == "host" else 1)
            self._mode_switching = False
            return

        self._save_controls_to_config()
        if self._runtime.running:
            self._runtime.stop(tcp_port=self._cfg.tcp_port)

        if not relaunch_as_mode(new_mode):
            QMessageBox.warning(self, "Neustart", "Neustart fehlgeschlagen.")
            self._mode_switching = True
            self.mode_combo.setCurrentIndex(0 if current == "host" else 1)
            self._mode_switching = False
            return

        save_mode(new_mode)
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _setup_tray(self) -> None:
        style = QApplication.style()
        tray_icon = QSystemTrayIcon(
            style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon),
            parent=self,
        )
        tray_icon.setToolTip("Alarmcast Host")
        menu = QMenu()
        open_action = QAction("Fenster anzeigen", menu)
        open_action.triggered.connect(self._show_window)
        menu.addAction(open_action)
        quit_action = QAction("Beenden", menu)
        quit_action.triggered.connect(self._exit_app)
        menu.addAction(quit_action)
        tray_icon.setContextMenu(menu)
        tray_icon.setToolTip("Alarmcast Host — laeuft im Hintergrund")
        tray_icon.activated.connect(self._on_tray_activated)
        tray_icon.show()
        self._tray_icon = tray_icon

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _update_status_display(self, text: str, mode: str) -> None:
        self._status_mode = mode
        self._status_title.setText(text)
        color = _STATUS_COLORS.get(mode, _STATUS_COLORS["idle"])
        self._status_dot.setStyleSheet(
            f"background-color: {color}; border-radius: 7px; min-width: 14px; max-width: 14px;"
        )
        if self._tray_icon is not None:
            clients = len(self._runtime.clients())
            suffix = f" | {clients} Client(s)" if self._runtime.running else ""
            self._tray_icon.setToolTip(f"Alarmcast Host — {text}{suffix}")

    def _update_reset_visibility(self) -> None:
        show_reset = self._runtime.running and self._runtime.alarm_active
        self.reset_button.setVisible(show_reset)

    def _start_runtime(self) -> None:
        try:
            self._save_controls_to_config()
            self._runtime.start(self._cfg)
        except Exception as exc:
            LOGGER.exception("Failed to start host runtime")
            QMessageBox.critical(self, "Start fehlgeschlagen", str(exc))
            self._update_status_display(f"Fehler: {exc}", "idle")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.send_message_button.setEnabled(True)
        self._update_status_display(f"Aktiv — Port {self._cfg.tcp_port}", "running")
        self._update_reset_visibility()

    def _stop_runtime(self) -> None:
        self._runtime.stop(tcp_port=self._cfg.tcp_port)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.send_message_button.setEnabled(False)
        self.clients_list.clear()
        self._update_status_display("Gestoppt", "idle")
        self._update_reset_visibility()
        self._refresh_event_log()

    def _reset_alarm(self) -> None:
        self._runtime.reset_alarm()
        append_event("reset_local")
        self._update_status_display("Alarm zurueckgesetzt", "running")
        self._update_reset_visibility()

    def _handle_remote_reset(self, client_name: str) -> None:
        self._runtime.reset_alarm()
        append_event("reset_remote", {"client": client_name})
        self._update_status_display(f"Reset von {client_name}", "running")
        self._update_reset_visibility()
        self._refresh_event_log()

    def _on_alarm_active_changed(self, active: bool) -> None:
        if not self._runtime.running:
            self._update_reset_visibility()
            return
        if active:
            self._update_status_display("Alarm aktiv", "alarm")
        else:
            self._update_status_display(f"Aktiv — Port {self._cfg.tcp_port}", "running")
        self._update_reset_visibility()

    def _message_mode_from_combo(self) -> MessageMode:
        index = self.message_mode_combo.currentIndex()
        if index == 1:
            return "info"
        if index == 2:
            return "request"
        return "status"

    def _send_broadcast_message(self) -> None:
        text = self.message_edit.text().strip()
        if not text:
            return
        if not self._runtime.running:
            QMessageBox.warning(self, "Nicht aktiv", "Server muss gestartet sein.")
            return
        mode = self._message_mode_from_combo()
        self._runtime.broadcast_message(text, mode=mode)
        self.message_edit.clear()
        self._last_message_label.setText(f"Gesendet ({mode}): {text}")
        self._refresh_event_log()

    def _refresh_clients(self) -> None:
        if not self._runtime.running:
            return
        clients = self._runtime.clients()
        self.clients_list.clear()
        for entry in clients:
            name = entry.split(" (", 1)[0]
            self.clients_list.addItem(f"● {name}")

    def _refresh_event_log(self) -> None:
        entries = read_recent()
        self.event_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            ts, label, details = format_event_row(entry)
            self.event_table.setItem(row, 0, QTableWidgetItem(ts))
            self.event_table.setItem(row, 1, QTableWidgetItem(label))
            self.event_table.setItem(row, 2, QTableWidgetItem(details))

    def _open_events_log(self) -> None:
        self._open_text_file(events_path(), "Ereignislog")

    def _open_runtime_log(self) -> None:
        self._open_text_file(get_config_dir() / "alarmcast.log", "Technisches Log")

    def _open_text_file(self, path: Path, title: str) -> None:
        if not path.exists():
            QMessageBox.information(self, title, f"Datei nicht gefunden:\n{path}")
            return
        try:
            subprocess.Popen(["notepad.exe", str(path)])
        except OSError as exc:
            QMessageBox.warning(self, title, f"Konnte Datei nicht oeffnen:\n{exc}")

    def _copy_psk(self) -> None:
        QGuiApplication.clipboard().setText(self._cfg.psk)

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _exit_app(self) -> None:
        if self._runtime.running:
            reply = QMessageBox.question(
                self,
                "Beenden",
                "Server wird gestoppt. Alarmcast wirklich beenden?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._shutdown_and_quit()

    def _shutdown_and_quit(self) -> None:
        self._save_controls_to_config()
        self._runtime.stop(tcp_port=self._cfg.tcp_port)
        if self._tray_icon is not None:
            self._tray_icon.hide()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
        if self._tray_icon is not None and not self._tray_hint_shown:
            self._tray_icon.showMessage(
                "Alarmcast Host",
                "Laeuft weiter im Infobereich. Rechtsklick zum Beenden.",
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )
            self._tray_hint_shown = True
