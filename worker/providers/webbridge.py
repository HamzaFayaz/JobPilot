"""Kimi WebBridge HTTP client — daemon health, start, and browser commands."""

from __future__ import annotations

import json
import logging
import os
import subprocess
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
                return WebBridgeStatus(
                    running=bool(data.get("running")),
                    extension_connected=bool(data.get("extension_connected")),
                    version=str(data.get("version") or ""),
                    extension_id=str(data.get("extension_id") or ""),
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
            return WebBridgeStatus(
                running=bool(data.get("running")),
                extension_connected=bool(data.get("extension_connected")),
                version=str(data.get("version") or ""),
                extension_id=str(data.get("extension_id") or ""),
            )
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError) as exc:
            logger.debug("WebBridge CLI status failed: %s", exc)
            return WebBridgeStatus(running=False, extension_connected=False)

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
            self.start_daemon()
            status = self.get_status()
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
