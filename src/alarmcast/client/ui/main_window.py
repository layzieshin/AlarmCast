"""Client mode main window with tabbed UI."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from alarmcast.client.message_overlay import MessageOverlayManager
from alarmcast.client.net import ClientNetwork
from alarmcast.client.output import AudioOutput, list_output_devices
from alarmcast.client.overlay import WarningOverlayManager
from alarmcast.core.autostart import set_windows_autostart
from alarmcast.core.config import load_client_config, save_client_config
from alarmcast.core.mode_switch import read_saved_mode, relaunch_as_mode, save_mode
from alarmcast.core.protocol import HostMessage

LOGGER = logging.getLogger(__name__)

_CLIENT_WINDOW_W = 460
_CLIENT_WINDOW_H = 560
_CONTENT_MARGINS = 10
_SETTINGS_ROW_SPACING = 6

_STATUS_COLORS = {
    "idle": "#9e9e9e",
    "connecting": "#1e88e5",
    "connected": "#43a047",
    "alarm": "#f9a825",
}


class _ClientSignals(QObject):
    status_changed = Signal(str)
    alarm_on = Signal()
    alarm_off = Signal()
    message_received = Signal(object)


class ClientWindow(QMainWindow):
    """Client settings and runtime controls."""

    def __init__(self) -> None:
        super().__init__()
        self._signals = _ClientSignals()
        self._signals.status_changed.connect(self._on_status)
        self._signals.alarm_on.connect(self._on_alarm_on)
        self._signals.alarm_off.connect(self._on_alarm_off)
        self._signals.message_received.connect(self._on_message_received)

        self._cfg = load_client_config()
        self._overlay = WarningOverlayManager()
        self._message_overlay = MessageOverlayManager()
        self._audio = AudioOutput(
            volume=self._cfg.volume,
            muted=self._cfg.muted,
            device_id=self._cfg.output_device_id if self._cfg.output_device_id >= 0 else None,
        )
        self._net = ClientNetwork(
            psk=self._cfg.psk,
            host_addr=self._cfg.host_addr,
            on_audio=self._audio.enqueue,
            on_alarm_on=self._signals.alarm_on.emit,
            on_alarm_off=self._signals.alarm_off.emit,
            on_status=self._signals.status_changed.emit,
            on_message=self._on_host_message,
        )
        self._tray_icon: QSystemTrayIcon | None = None
        self._running = False
        self._alarm_active = False
        self._mode_switching = False
        self._device_ids: list[int] = []
        self._tray_hint_shown = False
        self._device_needs_reconnect = False

        self.setWindowTitle("Alarmcast Client")
        self.setFixedSize(_CLIENT_WINDOW_W, _CLIENT_WINDOW_H)
        self._build_ui()
        self._load_config_into_controls()
        self._setup_tray()
        self._update_status_display("Bereit", "idle")
        self._update_reset_visibility()

        if self._cfg.autostart_with_windows:
            try:
                set_windows_autostart("client", True)
            except OSError as exc:
                LOGGER.warning("Autostart konnte nicht gesetzt werden: %s", exc)

        if self._cfg.auto_connect:
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

        self._message_label = QLabel("")
        self._message_label.setWordWrap(True)
        self._message_label.setStyleSheet("color: #1565c0; font-size: 9pt;")
        self._message_label.hide()
        overview_layout.addWidget(self._message_label)

        conn_row = QHBoxLayout()
        self.start_button = QPushButton("Verbinden")
        self.start_button.clicked.connect(self._start_runtime)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_runtime)
        self.stop_button.setEnabled(False)
        self.reset_button = QPushButton("Alarm zuruecksetzen")
        self.reset_button.setObjectName("primaryButton")
        self.reset_button.clicked.connect(self._send_reset)
        conn_row.addWidget(self.start_button)
        conn_row.addWidget(self.stop_button)
        conn_row.addWidget(self.reset_button)
        overview_layout.addLayout(conn_row)
        overview_layout.addStretch()

        tabs.addTab(overview, "Uebersicht")

        settings_page = QWidget()
        settings_outer = QVBoxLayout(settings_page)
        settings_outer.setContentsMargins(m, m, m, m)
        settings_outer.setSpacing(_SETTINGS_ROW_SPACING)

        settings_widget = QWidget()
        settings_layout = QGridLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setVerticalSpacing(_SETTINGS_ROW_SPACING)
        settings_layout.setHorizontalSpacing(8)

        row = 0
        settings_layout.addWidget(QLabel("Rolle"), row, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Host", "Client"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_combo_changed)
        settings_layout.addWidget(self.mode_combo, row, 1)
        row += 1

        settings_layout.addWidget(QLabel("Host-Adresse (leer = mDNS)"), row, 0)
        self.host_edit = QLineEdit()
        settings_layout.addWidget(self.host_edit, row, 1)
        row += 1

        settings_layout.addWidget(QLabel("PSK"), row, 0)
        self.psk_edit = QLineEdit()
        settings_layout.addWidget(self.psk_edit, row, 1)
        row += 1

        settings_layout.addWidget(QLabel("Ausgabegeraet"), row, 0, 1, 2)
        row += 1
        self.device_combo = QComboBox()
        self.device_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        settings_layout.addWidget(self.device_combo, row, 0, 1, 2)
        self._reload_devices()
        row += 1

        self._device_hint_label = QLabel("Neues Ausgabegeraet wird nach Neu verbinden aktiv.")
        self._device_hint_label.setStyleSheet("color: #5c6570; font-size: 9pt;")
        settings_layout.addWidget(self._device_hint_label, row, 0, 1, 2)
        row += 1

        self.reconnect_button = QPushButton("Neu verbinden")
        self.reconnect_button.clicked.connect(self._reconnect_runtime)
        self.reconnect_button.setEnabled(False)
        settings_layout.addWidget(self.reconnect_button, row, 0, 1, 2)
        row += 1

        settings_layout.addWidget(QLabel("Lautstaerke"), row, 0)
        vol_row = QHBoxLayout()
        self.volume_slider = QSlider()
        self.volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.valueChanged.connect(self._on_volume_slider)
        vol_row.addWidget(self.volume_slider, stretch=1)
        self.volume_label = QLabel("90 %")
        self.volume_label.setMinimumWidth(40)
        vol_row.addWidget(self.volume_label)
        settings_layout.addLayout(vol_row, row, 1)
        row += 1

        audio_row = QHBoxLayout()
        self.mute_button = QPushButton("Mute")
        self.mute_button.setCheckable(True)
        self.mute_button.setObjectName("muteButton")
        self.mute_button.toggled.connect(self._on_mute_changed)
        self.test_button = QPushButton("Testton")
        self.test_button.clicked.connect(self._play_test_tone)
        audio_row.addWidget(self.mute_button)
        audio_row.addWidget(self.test_button)
        settings_layout.addLayout(audio_row, row, 1)
        row += 1

        self.autostart_check = QCheckBox("Mit Windows starten")
        settings_layout.addWidget(self.autostart_check, row, 0, 1, 2)
        row += 1

        self.auto_connect_check = QCheckBox("Beim App-Start automatisch verbinden")
        settings_layout.addWidget(self.auto_connect_check, row, 0, 1, 2)
        row += 1

        self.message_overlay_check = QCheckBox("Nachrichten-Overlay (Info / Bestaetigung)")
        settings_layout.addWidget(self.message_overlay_check, row, 0, 1, 2)
        row += 1

        settings_outer.addWidget(settings_widget)

        save_row = QHBoxLayout()
        self.save_settings_button = QPushButton("Speichern")
        self.save_settings_button.setObjectName("primaryButton")
        self.save_settings_button.clicked.connect(self._on_save_settings_clicked)
        self._settings_saved_label = QLabel("")
        self._settings_saved_label.setStyleSheet("color: #43a047; font-size: 9pt;")
        save_row.addWidget(self.save_settings_button)
        save_row.addWidget(self._settings_saved_label, stretch=1)
        settings_outer.addLayout(save_row)

        tabs.addTab(settings_page, "Einstellungen")

    def _reload_devices(self) -> None:
        self.device_combo.clear()
        self._device_ids = []
        for dev_id, label in list_output_devices():
            self._device_ids.append(dev_id)
            self.device_combo.addItem(label)
        if self._cfg.output_device_id in self._device_ids:
            self.device_combo.setCurrentIndex(self._device_ids.index(self._cfg.output_device_id))
        elif -1 in self._device_ids:
            self.device_combo.setCurrentIndex(self._device_ids.index(-1))

    def _load_config_into_controls(self) -> None:
        self._mode_switching = True
        saved = read_saved_mode() or "client"
        self.mode_combo.setCurrentIndex(0 if saved == "host" else 1)
        self._mode_switching = False

        self.host_edit.setText(self._cfg.host_addr)
        self.psk_edit.setText(self._cfg.psk)
        self.volume_slider.setValue(int(round(self._cfg.volume * 100)))
        self.volume_label.setText(f"{self.volume_slider.value()} %")
        self.mute_button.setChecked(self._cfg.muted)
        self.autostart_check.setChecked(self._cfg.autostart_with_windows)
        self.auto_connect_check.setChecked(self._cfg.auto_connect)
        self.message_overlay_check.setChecked(self._cfg.message_overlay_enabled)

    def _on_save_settings_clicked(self) -> None:
        previous_device = self._cfg.output_device_id
        self._save_controls_to_config()
        if self._running and previous_device != self._cfg.output_device_id:
            self._device_needs_reconnect = True
            self.reconnect_button.setEnabled(True)
            self._settings_saved_label.setText(
                "Gespeichert. Neues Ausgabegeraet aktiv nach Neu verbinden."
            )
            QTimer.singleShot(5000, self._settings_saved_label.clear)
            return
        self._apply_runtime_from_config()
        self._settings_saved_label.setText("Einstellungen gespeichert.")
        QTimer.singleShot(4000, self._settings_saved_label.clear)

    def _apply_runtime_from_config(self) -> None:
        if not self._running:
            return
        self._audio.set_volume(self._cfg.volume)
        self._audio.set_muted(self._cfg.muted)
        self._net.set_psk(self._cfg.psk)
        self._net.set_host_addr(self._cfg.host_addr)

    def _reconnect_runtime(self) -> None:
        if not self._running:
            return
        self._stop_runtime()
        self._start_runtime()
        self._device_needs_reconnect = False
        self.reconnect_button.setEnabled(False)
        self._settings_saved_label.setText("Neu verbunden. Ausgabegeraet aktiv.")
        QTimer.singleShot(4000, self._settings_saved_label.clear)

    def _save_controls_to_config(self) -> None:
        self._cfg.host_addr = self.host_edit.text().strip()
        self._cfg.psk = self.psk_edit.text().strip()
        self._cfg.volume = self.volume_slider.value() / 100.0
        self._cfg.muted = self.mute_button.isChecked()
        self._cfg.autostart_with_windows = self.autostart_check.isChecked()
        self._cfg.auto_connect = self.auto_connect_check.isChecked()
        self._cfg.message_overlay_enabled = self.message_overlay_check.isChecked()
        if self.device_combo.currentIndex() >= 0:
            self._cfg.output_device_id = self._device_ids[self.device_combo.currentIndex()]
        save_client_config(self._cfg)
        try:
            set_windows_autostart("client", self._cfg.autostart_with_windows)
        except OSError as exc:
            LOGGER.warning("Autostart update failed: %s", exc)

    def _on_mode_combo_changed(self, index: int) -> None:
        if self._mode_switching:
            return
        new_mode = "host" if index == 0 else "client"
        current = read_saved_mode() or "client"
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
        if self._running:
            self._stop_runtime()

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
            style.standardIcon(QStyle.StandardPixmap.SP_MediaVolume),
            parent=self,
        )
        tray_icon.setToolTip("Alarmcast Client")
        menu = QMenu()
        open_action = QAction("Fenster anzeigen", menu)
        open_action.triggered.connect(self._show_window)
        menu.addAction(open_action)
        quit_action = QAction("Beenden", menu)
        quit_action.triggered.connect(self._exit_app)
        menu.addAction(quit_action)
        tray_icon.setContextMenu(menu)
        tray_icon.setToolTip("Alarmcast Client — laeuft im Hintergrund")
        tray_icon.activated.connect(self._on_tray_activated)
        tray_icon.show()
        self._tray_icon = tray_icon

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _on_host_message(self, message: HostMessage) -> None:
        self._signals.message_received.emit(message)

    def _update_status_display(self, text: str, mode: str) -> None:
        self._status_title.setText(text)
        color = _STATUS_COLORS.get(mode, _STATUS_COLORS["idle"])
        self._status_dot.setStyleSheet(
            f"background-color: {color}; border-radius: 7px; min-width: 14px; max-width: 14px;"
        )
        if self._tray_icon is not None:
            self._tray_icon.setToolTip(f"Alarmcast Client — {text}")

    def _update_reset_visibility(self) -> None:
        self.reset_button.setVisible(self._alarm_active)

    def _status_mode_from_text(self, text: str) -> str:
        lower = text.lower()
        if "verbunden" in lower and "verloren" not in lower and "fehl" not in lower:
            return "connected"
        if "alarm" in lower or self._alarm_active:
            return "alarm"
        if "suche" in lower or "verbinde" in lower:
            return "connecting"
        if self._running:
            return "connecting"
        return "idle"

    def _start_runtime(self) -> None:
        try:
            self._save_controls_to_config()
            dev_id = self._cfg.output_device_id if self._cfg.output_device_id >= 0 else None
            self._audio.set_device(dev_id)
            self._audio.set_volume(self._cfg.volume)
            self._audio.set_muted(self._cfg.muted)
            self._net.set_psk(self._cfg.psk)
            self._net.set_host_addr(self._cfg.host_addr)
            self._audio.start()
            self._net.start()
            self._running = True
        except Exception as exc:
            LOGGER.exception("Client start failed")
            QMessageBox.critical(self, "Start fehlgeschlagen", str(exc))
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self._device_needs_reconnect = False
        self.reconnect_button.setEnabled(False)
        self._update_status_display("Verbindung wird aufgebaut ...", "connecting")

    def _stop_runtime(self) -> None:
        self._running = False
        self._net.stop()
        self._audio.stop()
        self._overlay.hide()
        self._alarm_active = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self._device_needs_reconnect = False
        self.reconnect_button.setEnabled(False)
        self._update_status_display("Gestoppt", "idle")
        self._update_reset_visibility()

    def _send_reset(self) -> None:
        self._net.send_reset()
        self._overlay.hide()
        self._alarm_active = False
        self._update_reset_visibility()
        self._update_status_display("Reset gesendet", "connected")

    def _play_test_tone(self) -> None:
        if not self._audio.play_test_tone():
            QMessageBox.warning(self, "Testton", "Testton konnte nicht abgespielt werden.")

    def _on_volume_slider(self, value: int) -> None:
        vol = value / 100.0
        self.volume_label.setText(f"{value} %")
        self._audio.set_volume(vol)
        self._cfg.volume = vol

    def _on_mute_changed(self, checked: bool) -> None:
        self._audio.set_muted(checked)
        self._cfg.muted = checked
        self.mute_button.setText("Stumm" if checked else "Mute")

    def _on_status(self, text: str) -> None:
        mode = self._status_mode_from_text(text)
        if self._alarm_active and mode == "connected":
            mode = "alarm"
        self._update_status_display(text, mode)

    def _on_alarm_on(self) -> None:
        self._alarm_active = True
        self._overlay.show()
        self._update_status_display("Alarm aktiv", "alarm")
        self._update_reset_visibility()

    def _on_alarm_off(self) -> None:
        self._alarm_active = False
        self._overlay.hide()
        self._update_reset_visibility()
        if self._net.connected:
            self._update_status_display("Verbunden", "connected")
        elif self._running:
            self._update_status_display("Verbindung aktiv", "connecting")
        else:
            self._update_status_display("Gestoppt", "idle")

    def _on_message_received(self, message: object) -> None:
        if not isinstance(message, HostMessage):
            return
        self._message_label.setText(f"Nachricht: {message.text}")
        self._message_label.show()
        if self._cfg.message_overlay_enabled and message.mode in ("info", "request"):
            self._message_overlay.show_message(message)
        else:
            self._message_overlay.hide()

    def _show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _exit_app(self) -> None:
        if self._running:
            reply = QMessageBox.question(
                self,
                "Beenden",
                "Verbindung wird getrennt. Alarmcast wirklich beenden?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._shutdown_and_quit()

    def _shutdown_and_quit(self) -> None:
        self._save_controls_to_config()
        if self._running:
            self._stop_runtime()
        self._message_overlay.hide()
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
                "Alarmcast Client",
                "Laeuft weiter im Infobereich. Rechtsklick zum Beenden.",
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )
            self._tray_hint_shown = True
