"""Kimi WebBridge HTTP client — daemon health, start, and browser commands."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Matches backend.app.models.browser.BrowserHealth string values.
HEALTH_READY = "ready"
HEALTH_NOT_INSTALLED = "not_installed"
HEALTH_DAEMON_DOWN = "daemon_down"
HEALTH_ERROR = "error"


@dataclass
class WebBridgeStatus:
    running: bool = False
    extension_connected: bool = False
    version: str = ""
    extension_id: str = ""
    pid: int | None = None
    note: str = ""


_RECOVERY_COOLDOWN_SECONDS = 30.0


def _daemon_home() -> Path:
    return Path(os.environ.get("USERPROFILE") or Path.home()) / ".kimi-webbridge"


def _daemon_pid_file() -> Path:
    return _daemon_home() / "daemon.pid"


def _is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _daemon_binary() -> Path | None:
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    candidates = [
        home / ".kimi-webbridge" / "bin" / "kimi-webbridge.exe",
        home / ".kimi-webbridge" / "bin" / "kimi-webbridge",
        Path("/usr/local/bin/kimi-webbridge"),
        Path.home() / ".kimi-webbridge" / "bin" / "kimi-webbridge",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


class WebBridgeClient:
    def __init__(self, base_url: str = "http://127.0.0.1:10086") -> None:
        self._base = base_url.rstrip("/")
        self._last_recovery_at: float = 0.0

    def get_status(self) -> WebBridgeStatus:
        status = self._status_via_http()
        if status is not None:
            return status
        return self._status_via_cli()

    def _status_via_http(self) -> WebBridgeStatus | None:
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"{self._base}/status")
                if response.status_code != 200:
                    return None
                data = response.json()
                pid = data.get("pid")
                return WebBridgeStatus(
                    running=bool(data.get("running")),
                    extension_connected=bool(data.get("extension_connected")),
                    version=str(data.get("version") or ""),
                    extension_id=str(data.get("extension_id") or ""),
                    pid=int(pid) if pid else None,
                    note=str(data.get("note") or ""),
                )
        except (httpx.HTTPError, json.JSONDecodeError, ValueError):
            return None

    def _status_via_cli(self) -> WebBridgeStatus:
        binary = _daemon_binary()
        if not binary:
            return WebBridgeStatus(running=False, extension_connected=False)
        try:
            result = subprocess.run(
                [str(binary), "status"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0 and not result.stdout.strip():
                return WebBridgeStatus(running=False, extension_connected=False)
            data = json.loads(result.stdout)
            pid = data.get("pid")
            return WebBridgeStatus(
                running=bool(data.get("running")),
                extension_connected=bool(data.get("extension_connected")),
                version=str(data.get("version") or ""),
                extension_id=str(data.get("extension_id") or ""),
                pid=int(pid) if pid else None,
                note=str(data.get("note") or ""),
            )
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as exc:
            logger.debug("WebBridge CLI status failed: %s", exc)
            return WebBridgeStatus(running=False, extension_connected=False)

    def _read_pid_file(self) -> int | None:
        path = _daemon_pid_file()
        if not path.is_file():
            return None
        try:
            return int(path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    def _daemon_is_stuck(self, status: WebBridgeStatus) -> bool:
        if status.running and status.extension_connected:
            return False
        if status.running:
            return False

        note = status.note.lower()
        if "stuck" in note or "http probe failed" in note:
            return True

        pid = status.pid or self._read_pid_file()
        if pid is not None and not _is_pid_alive(pid):
            return True

        if self._status_via_http() is None and _daemon_pid_file().is_file():
            return True

        return False

    def _recover_stale_daemon(self) -> bool:
        now = time.monotonic()
        if now - self._last_recovery_at < _RECOVERY_COOLDOWN_SECONDS:
            return False
        self._last_recovery_at = now

        pid = self._read_pid_file()
        logger.info(
            "WebBridge daemon looks stuck (pid=%s) — clearing stale lock and restarting",
            pid or "unknown",
        )

        path = _daemon_pid_file()
        if path.is_file():
            try:
                path.unlink()
            except OSError as exc:
                logger.warning("Could not remove stale WebBridge pid file: %s", exc)
                return False

        return self.start_daemon()

    def start_daemon(self) -> bool:
        binary = _daemon_binary()
        if not binary:
            logger.warning("Kimi WebBridge binary not found — user must install it.")
            return False
        try:
            result = subprocess.run(
                [str(binary), "start"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if result.returncode != 0:
                logger.warning("kimi-webbridge start exited %s: %s", result.returncode, result.stderr)
            return True
        except (subprocess.SubprocessError, OSError) as exc:
            logger.warning("Failed to start WebBridge daemon: %s", exc)
            return False

    def check_health(self, *, auto_start_daemon: bool = True) -> str:
        status = self.get_status()
        if not status.running and auto_start_daemon:
            if self._daemon_is_stuck(status):
                self._recover_stale_daemon()
            else:
                self.start_daemon()
            time.sleep(1.0)
            status = self.get_status()
            if status.running and not status.extension_connected:
                logger.info(
                    "WebBridge daemon is up — waiting for Chrome extension to connect"
                )
        if not status.running:
            return HEALTH_DAEMON_DOWN
        if not status.extension_connected:
            return HEALTH_NOT_INSTALLED
        return HEALTH_READY

    async def command(
        self,
        action: str,
        args: dict[str, Any] | None = None,
        *,
        session: str,
    ) -> dict[str, Any]:
        payload = {
            "action": action,
            "args": args or {},
            "session": session,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self._base}/command", json=payload)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
            return {"value": data}
