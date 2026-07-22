# Initialer Projekt-Setup-Plan

Dieser Plan beschreibt die Bauphasen. **Phase 1 ist mit Erstellung dieses Plans abgeschlossen.** Phase 2+ erfolgt in separaten Sessions nach Freigabe.

## Phase 1 — Doku und Geruest (DONE)

- `AGENTS.md`
- `.cursor/rules/*.mdc` (project-architecture, safe-existing-file-edits, verification, code-style)
- `docs/project-brief.md`, `docs/architecture.md`
- `docs/decisions/README.md`, `docs/decisions/0001-initial-architecture.md` (Status: accepted)
- `README.md`, `.gitignore`
- Dieser Plan

## Phase 2 — Projektgeruest und Toolchain

1. `pyproject.toml` mit Dependencies:
   - runtime: `PySide6`, `soundcard`, `sounddevice`, `numpy==1.26.4`, `zeroconf`
   - dev: `pyinstaller`, `ruff`, `mypy`, `pytest`
2. `src/alarmcast/__main__.py` mit Argparse `--host | --client`. Delegiert an `host.app.run()` bzw. `client.app.run()`.
3. Minimal-Qt-Tray fuer beide Modi (kein Audio, kein Netz). Zeigt nur "Alarmcast Host" bzw. "Alarmcast Client" Tray-Icon und ein leeres Settings-Fenster.
4. `core/logging_setup.py` als erstes echtes Core-Modul (wird ab Phase 3 von allen genutzt).
5. Pruefung: `ruff check`, `ruff format --check`, `mypy src`, `pytest` (mit Dummy-Test) laufen gruen.

## Phase 3 — Core

6. `core/audio_format.py`: Konstanten 48 kHz / Mono / int16 / 20 ms.
7. `core/protocol.py`: Framing + `send_frame` mit Lock + `recv_frame` mit korrektem Timeout-Verhalten.
8. `core/alarm_logic.py`: pure Klasse `AlarmDetector(threshold, signal_target, window_seconds)` mit Methoden `update(rms) -> AlarmEvent`, `reset()`. Unit-Tests.
9. `core/config.py`: Lader/Schreiber fuer `%APPDATA%\AlarmCast\{host,client}.json`. PSK-Erststart-Logik.
10. `core/security.py`: `generate_psk()`, `verify_psk(expected, given)` (konstanzeitiger Vergleich via `hmac.compare_digest`).
11. `core/discovery.py`: `publish_host(port)` und `browse_for_host(timeout)` mit `zeroconf`.

## Phase 4 — Host

12. `host/capture.py`: `soundcard` Loopback, liefert 20 ms PCM-Frames in eine Queue.
13. `host/server.py`: TCP `:50050`, akzeptiert Verbindungen, prueft PSK aus HELLO, fuehrt pro Client einen Send-Lock, broadcastet Audio + Control.
14. `host/detector.py`: verdrahtet `capture` -> `alarm_logic` -> `server`. Sendet `ALM_ON` / `ALM_OFF`.
15. `host/app.py`: Qt-Tray + Settings-Fenster (Threshold-Regler, Signal-Anzahl, Window-Sekunden, PSK-Anzeige, Clientliste, Start/Stop, Reset).

## Phase 5 — Client

16. `client/net.py`: mDNS-Browse + Fallback-Adresse, Auto-Reconnect, blockierendes Lesen.
17. `client/output.py`: `sounddevice` Output mit Mute/Volume aus Config.
18. `client/overlay.py`: Qt Multi-Monitor Overlay, `WA_TranslucentBackground` + Frameless + Topmost, Fade via `QGraphicsOpacityEffect`.
19. `client/app.py`: Qt-Tray + Settings (Lautstaerke, Mute, Output-Device, Host-Adresse, PSK, Autostart-Toggle), Reset-Button.

## Phase 6 — Build und Verifikation

20. PyInstaller-Spec: `--onefile --noconsole --name alarmcast --collect-all soundcard --collect-all sounddevice --collect-all numpy --collect-all zeroconf`. Beide Modi in einer EXE.
21. `tests/manual_smoke.md`: manuelle Pruefliste fuer 1 Host + 2 Clients (Vorlage in `.cursor/rules/verification.mdc`).

## Offene Punkte / Future-Work

- PSK-Verteilung per QR-Code im Host-GUI.
- Diagnose-Tab im Host (Frames/s, RMS, Restzeit im Fenster, verbundene Clients).
- Mehrsprachigkeit (aktuell deutsch).
- Code-Signing der EXE (optional, falls AV trotzdem stutzt).
