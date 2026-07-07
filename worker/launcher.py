"""PySide6 shell for Search Helper — setup UI, tray, logs; worker runs in subprocess."""

from __future__ import annotations

import logging
import os
import re
import sys

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from worker.local_config import (
    DEFAULT_API_BASE,
    DEFAULT_MODEL,
    apply_config_to_environ,
    load_config,
    save_config,
)
from worker.runtime_paths import is_frozen, repo_root
from worker.ui import asset_path, load_stylesheet
from worker.ui.logs_window import LogWindow
from worker.ui.settings_panel import SettingsPanel
from worker.ui.widgets import (
    WEBBRIDGE_INSTALL_URL,
    ConnectionSummaryCard,
    StatusBanner,
    WebBridgeInstallCard,
)

_STATUS_SETUP = "Open Settings to add your pairing code and API key"
_STATUS_READY_TO_START = "Ready — click Start to connect"
_STATUS_STARTING = "Starting Search Helper…"
_STATUS_READY = "Connected · Ready to search"
_STATUS_WAITING = "Waiting for search…"
_STATUS_STOPPING = "Stopping…"
_STATUS_WEBBRIDGE_CHROME = "Open Chrome — extension not connected"
_STATUS_WEBBRIDGE_DAEMON = "Starting WebBridge…"
_AUTO_STOP_DELAY_MS = 2000


class LogEmitter(QObject):
    line = Signal(str)


class SearchHelperWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("JobPilot Search Helper")
        self.setMinimumSize(400, 480)
        self.resize(420, 520)

        self._process: QProcess | None = None
        self._log_emitter = LogEmitter()
        self._log_emitter.line.connect(self._append_log)
        self._saved_config = load_config()
        self._webbridge_issue = False
        self._worker_running = False
        self._auto_stop_scheduled = False
        self._intentional_stop = False
        self._log_lines: list[str] = []
        self._log_window: LogWindow | None = None

        self._build_ui()
        self._build_tray()
        self._apply_icon()
        self._refresh_home_state()

        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(lambda: self._inline_notice.hide())

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("Root")
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_tab_bar())

        self._stack = QStackedWidget()
        self._home_page = self._build_home_page()
        self._settings_panel = SettingsPanel()
        self._settings_panel.saved.connect(self._save_settings)
        self._stack.addWidget(self._home_page)
        self._stack.addWidget(self._settings_panel)
        root_layout.addWidget(self._stack, 1)

        self.setCentralWidget(central)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("AppHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(20, 14, 20, 10)

        mark = QLabel("JP")
        mark.setObjectName("BrandMark")

        titles = QVBoxLayout()
        titles.setSpacing(0)
        title = QLabel("JobPilot Search Helper")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Runs on this PC")
        subtitle.setObjectName("AppSubtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)

        row.addWidget(mark, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(titles, 1)
        return header

    def _build_tab_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TabBar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(20, 0, 20, 0)
        row.setSpacing(6)

        self._home_tab = QPushButton("Home")
        self._home_tab.setObjectName("TabButton")
        self._home_tab.setCheckable(True)
        self._home_tab.setChecked(True)
        self._home_tab.clicked.connect(lambda: self._show_page(0))

        self._settings_tab = QPushButton("Settings")
        self._settings_tab.setObjectName("TabButton")
        self._settings_tab.setCheckable(True)
        self._settings_tab.clicked.connect(self._open_settings)

        row.addWidget(self._home_tab)
        row.addWidget(self._settings_tab)
        row.addStretch(1)
        return bar

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 12, 20, 16)
        layout.setSpacing(14)

        self._status_banner = StatusBanner()
        layout.addWidget(self._status_banner)

        self._summary_card = ConnectionSummaryCard()
        layout.addWidget(self._summary_card)

        self._webbridge_card = WebBridgeInstallCard()
        self._webbridge_card.hide()
        layout.addWidget(self._webbridge_card)

        layout.addLayout(self._build_actions())

        self._inline_notice = QLabel()
        self._inline_notice.setObjectName("InlineNotice")
        self._inline_notice.hide()
        layout.addWidget(self._inline_notice)

        logs_row = QHBoxLayout()
        self._logs_button = QPushButton("View logs")
        self._logs_button.setObjectName("SecondaryButton")
        self._logs_button.clicked.connect(self._open_logs_window)
        logs_row.addWidget(self._logs_button, 0, Qt.AlignmentFlag.AlignLeft)
        logs_row.addStretch(1)
        layout.addLayout(logs_row)

        layout.addWidget(self._build_footer())
        layout.addStretch(1)
        return page

    def _build_actions(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        self._start_button = QPushButton("Start")
        self._start_button.setObjectName("PrimaryButton")
        self._start_button.clicked.connect(self._start_worker)

        self._stop_button = QPushButton("Stop")
        self._stop_button.setObjectName("DangerButton")
        self._stop_button.clicked.connect(self._stop_worker)
        self._stop_button.setEnabled(False)

        row.addWidget(self._start_button, 2)
        row.addWidget(self._stop_button, 1)
        return row

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        col = QVBoxLayout(footer)
        col.setContentsMargins(0, 4, 0, 0)
        col.setSpacing(4)

        link = QLabel(f'<a href="{WEBBRIDGE_INSTALL_URL}">Install Kimi WebBridge</a>')
        link.setObjectName("FooterLink")
        link.setOpenExternalLinks(True)

        hint = QLabel("Closing this window keeps Search Helper running in the system tray.")
        hint.setObjectName("FooterHint")
        hint.setWordWrap(True)

        col.addWidget(link, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(hint, 0, Qt.AlignmentFlag.AlignHCenter)
        return footer

    def _build_tray(self) -> None:
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("JobPilot Search Helper")
        menu = QMenu(self)

        show_action = QAction("Show window", self)
        show_action.triggered.connect(self._show_home)
        menu.addAction(show_action)

        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        logs_action = QAction("View logs", self)
        logs_action.triggered.connect(self._open_logs_window)
        menu.addAction(logs_action)

        menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._tray_activated)
        self._tray.show()

    def _apply_icon(self) -> None:
        icon_path = asset_path("icon.ico")
        if not icon_path.is_file():
            icon_path = asset_path("icon.png")
        if icon_path.is_file():
            icon = QIcon(str(icon_path))
            self.setWindowIcon(icon)
            self._tray.setIcon(icon)

    def _open_logs_window(self) -> None:
        if self._log_window is None:
            self._log_window = LogWindow(self)
            if icon := self.windowIcon():
                self._log_window.setWindowIcon(icon)
            self._log_window.set_content("\n".join(self._log_lines))
        else:
            self._log_window.set_content("\n".join(self._log_lines))
        self._log_window.show()
        self._log_window.raise_()
        self._log_window.activateWindow()

    def _show_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._home_tab.setChecked(index == 0)
        self._settings_tab.setChecked(index == 1)

    def _show_home(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._show_page(0)
        self._refresh_home_state()

    def _open_settings(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._saved_config = load_config()
        self._settings_panel.load_from_disk(self._saved_config)
        self._show_page(1)

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_home()

    def _effective_config(self) -> dict[str, str]:
        disk = load_config()
        if self._stack.currentIndex() == 1 and self._settings_panel.is_editing():
            form = self._settings_panel.collect()
            token = form["worker_token"]
            api_key = form["dashscope_api_key"]
            model = form["qwen_model"]
        else:
            token = disk.get("worker_token", "")
            api_key = disk.get("dashscope_api_key", "")
            model = disk.get("qwen_model", "") or DEFAULT_MODEL

        return {
            "jobpilot_api_base": DEFAULT_API_BASE,
            "worker_token": token.strip(),
            "dashscope_api_key": api_key.strip(),
            "qwen_model": model.strip() or DEFAULT_MODEL,
        }

    def _credentials_complete(self, cfg: dict[str, str] | None = None) -> bool:
        data = cfg or self._effective_config()
        return bool(data.get("worker_token") and data.get("dashscope_api_key"))

    def _refresh_home_state(self) -> None:
        self._saved_config = load_config()
        self._summary_card.update_from_config(self._saved_config)

        if self._worker_running:
            return

        if self._webbridge_issue:
            self._status_banner.set_status(
                _STATUS_WEBBRIDGE_CHROME,
                kind="warning",
                hint="Install WebBridge and open Chrome with the extension connected.",
            )
            self._webbridge_card.show()
        elif self._credentials_complete(self._saved_config):
            self._status_banner.set_status(_STATUS_READY_TO_START, kind="success")
            self._webbridge_card.hide()
        else:
            self._status_banner.set_status(
                _STATUS_SETUP,
                kind="neutral",
                hint="Go to the Settings tab to connect this computer.",
            )
            self._webbridge_card.hide()

        self._start_button.setEnabled(self._credentials_complete() and not self._worker_running)

    def _validate(self, cfg: dict[str, str]) -> str | None:
        if not cfg["worker_token"]:
            return "Pairing code is required. Add it in Settings."
        if not cfg["dashscope_api_key"]:
            return "Dashscope API key is required. Add it in Settings."
        return None

    def _show_notice(self, text: str) -> None:
        self._inline_notice.setText(text)
        self._inline_notice.show()
        self._notice_timer.start(4000)

    def _save_settings(self) -> None:
        cfg = self._effective_config()
        error = self._validate(cfg)
        if error:
            QMessageBox.warning(self, "Missing settings", error)
            return
        save_config(**cfg)
        self._saved_config = load_config()
        self._settings_panel.load_from_disk(self._saved_config)
        self._refresh_home_state()
        self._append_log("Settings saved.")
        self._show_notice("Settings saved")
        self._show_page(0)

    def _worker_command(self) -> list[str]:
        if is_frozen():
            return [sys.executable, "--worker-internal"]
        return [sys.executable, "-m", "worker.app_entry", "--worker-internal"]

    def _start_worker(self) -> None:
        if self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning:
            return

        cfg = self._effective_config()
        error = self._validate(cfg)
        if error:
            QMessageBox.warning(self, "Setup required", error)
            self._open_settings()
            return

        save_config(**cfg)
        apply_config_to_environ(cfg)

        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._read_worker_output)
        self._process.finished.connect(self._worker_finished)
        if not is_frozen():
            self._process.setWorkingDirectory(str(repo_root()))

        env = QProcessEnvironment.systemEnvironment()
        for key, value in os.environ.items():
            if key.upper().startswith(
                ("JOBPILOT_", "WORKER_", "DASHSCOPE_", "QWEN_", "BROWSER_", "WEBBRIDGE_", "POLL_", "AGENT_")
            ):
                env.insert(key, value)
        self._process.setProcessEnvironment(env)

        cmd = self._worker_command()
        self._worker_running = True
        self._auto_stop_scheduled = False
        self._intentional_stop = False
        self._webbridge_issue = False
        self._set_status(_STATUS_STARTING, kind="info")
        self._append_log("Starting worker process…")
        self._process.start(cmd[0], cmd[1:])
        self._start_button.setEnabled(False)
        self._stop_button.setEnabled(True)

    def _read_worker_output(self) -> None:
        if not self._process:
            return
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            text = line.rstrip()
            if text:
                self._log_emitter.line.emit(text)
                self._update_status_from_log(text)

    def _schedule_auto_stop(self) -> None:
        if self._auto_stop_scheduled or not self._worker_running:
            return
        self._auto_stop_scheduled = True
        self._append_log("Search complete — stopping worker shortly…")
        QTimer.singleShot(_AUTO_STOP_DELAY_MS, self._auto_stop_after_success)

    def _auto_stop_after_success(self) -> None:
        if self._worker_running and self._process is not None:
            self._stop_worker()

    def _update_status_from_log(self, line: str) -> None:
        lower = line.lower()

        if "received task" in lower:
            role = self._parse_role_from_log(line)
            if role:
                self._set_status(f"Searching LinkedIn for {role}…", kind="info")
            else:
                self._set_status("Searching LinkedIn…", kind="info")
            return

        if "posted" in lower and "listings" in lower:
            match = re.search(r"posted\s+(\d+)\s+listings", lower)
            if match:
                self._set_status(
                    f"Found {match.group(1)} jobs — sent to JobPilot",
                    kind="success",
                    hint="Worker will stop automatically.",
                )
            else:
                self._set_status(
                    "Search finished — results sent to JobPilot",
                    kind="success",
                    hint="Worker will stop automatically.",
                )
            self._schedule_auto_stop()
            return

        if "webbridge ready" in lower:
            self._webbridge_issue = False
            self._webbridge_card.hide()
            self._set_status(_STATUS_READY, kind="success")
            return

        if "daemon down" in lower or ("daemon running" in lower and "extension" in lower):
            self._webbridge_issue = True
            status = _STATUS_WEBBRIDGE_DAEMON if "daemon down" in lower else _STATUS_WEBBRIDGE_CHROME
            self._set_status(status, kind="warning")
            self._webbridge_card.show()
            return

        if "extension" in lower and ("not connected" in lower or "open chrome" in lower):
            self._webbridge_issue = True
            self._set_status(_STATUS_WEBBRIDGE_CHROME, kind="warning")
            self._webbridge_card.show()
            return

        if "polling for tasks" in lower or "search helper starting" in lower:
            self._set_status(_STATUS_WAITING, kind="success", hint="Start a search from the JobPilot website.")
            return

        if "not ready" in lower and "webbridge" in lower:
            self._webbridge_issue = True
            self._set_status(_STATUS_WEBBRIDGE_CHROME, kind="warning")
            self._webbridge_card.show()

    @staticmethod
    def _parse_role_from_log(line: str) -> str | None:
        match = re.search(r"\(([^/]+)\s*/", line)
        return match.group(1).strip() if match else None

    def _worker_finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        intentional = self._intentional_stop
        self._worker_running = False
        self._auto_stop_scheduled = False
        self._intentional_stop = False
        self._stop_button.setEnabled(False)
        self._process = None
        if exit_code == 0 or intentional:
            self._append_log("Worker stopped.")
            self._refresh_home_state()
        else:
            self._set_status(f"Worker stopped unexpectedly (code {exit_code})", kind="error")
            self._append_log(f"Worker exited with code {exit_code}.")
            self._start_button.setEnabled(True)

    def _stop_worker(self) -> None:
        if self._process is None:
            return
        self._intentional_stop = True
        self._set_status(_STATUS_STOPPING, kind="info")
        self._append_log("Stopping worker…")
        self._process.terminate()
        if not self._process.waitForFinished(5000):
            self._process.kill()

    def _set_status(self, text: str, *, kind: str = "neutral", hint: str | None = None) -> None:
        self._status_banner.set_status(text, kind=kind, hint=hint)
        self._tray.setToolTip(f"JobPilot Search Helper — {text}")

    def _append_log(self, line: str) -> None:
        self._log_lines.append(line)
        if len(self._log_lines) > 5000:
            self._log_lines = self._log_lines[-5000:]
        if self._log_window is not None and self._log_window.isVisible():
            self._log_window.append_line(line)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._tray.isVisible():
            self.hide()
            self._tray.showMessage(
                "JobPilot Search Helper",
                "Still running in the system tray.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            event.ignore()
            return
        if self._log_window is not None:
            self._log_window.close()
        self._stop_worker()
        event.accept()

    def _quit_app(self) -> None:
        if self._log_window is not None:
            self._log_window.close()
        self._stop_worker()
        self._tray.hide()
        QApplication.instance().quit()


def run_launcher() -> None:
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    app.setApplicationName("JobPilot Search Helper")
    app.setQuitOnLastWindowClosed(False)

    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    window = SearchHelperWindow()
    window.show()
    sys.exit(app.exec())
