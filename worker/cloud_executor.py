"""Thin WebBridge tool executor for cloud ReAct mode (no local Dashscope)."""

from __future__ import annotations

import logging
from typing import Any

from worker.api_client import JobPilotWorkerClient
from worker.config import WorkerSettings
from worker.models import WorkerTask
from worker.providers.webbridge import WebBridgeClient

logger = logging.getLogger(__name__)


async def run_cloud_tool_executor(
    task: WorkerTask,
    settings: WorkerSettings,
    api: JobPilotWorkerClient,
) -> None:
    """Execute browser tools commanded by the backend cloud agent until done."""
    webbridge = WebBridgeClient(settings.webbridge_url)
    health = webbridge.check_health(auto_start_daemon=True)
    if health != "ready":
        if health == "daemon_down":
            raise RuntimeError(
                "Kimi WebBridge daemon is not running. Install WebBridge and run: kimi-webbridge.exe start"
            )
        raise RuntimeError(
            "Kimi WebBridge extension is not connected. Open Chrome with the WebBridge extension installed."
        )

    logger.info(
        "Cloud executor attached: task=%s run=%s platform=%s",
        task.task_id,
        task.run_id,
        task.platform,
    )
    api.attach_cloud_agent(task.task_id)

    idle_polls = 0
    while True:
        command = api.poll_agent_command(task.task_id, timeout_seconds=25.0)
        if command is None:
            idle_polls += 1
            if idle_polls == 1 or idle_polls % 12 == 0:
                logger.info(
                    "Cloud executor waiting for tool command (task=%s polls=%s)",
                    task.task_id,
                    idle_polls,
                )
            continue

        idle_polls = 0
        cmd_type = str(command.get("type") or "")
        if cmd_type == "done":
            logger.info("Cloud agent finished task %s", task.task_id)
            return
        if cmd_type == "fail":
            error = command.get("error") or "Cloud agent failed"
            code = command.get("code") or "cloud_agent_failed"
            raise RuntimeError(f"{code}: {error}")

        if cmd_type != "tool":
            logger.warning("Ignoring unknown agent command type=%s", cmd_type)
            continue

        call_id = str(command.get("callId") or "")
        name = str(command.get("name") or "")
        session = str(command.get("session") or f"jobpilot-run-{task.run_id}")
        arguments = command.get("arguments") or {}
        if not isinstance(arguments, dict):
            arguments = {}

        if not call_id or not name:
            logger.warning("Invalid tool command missing callId/name: %s", command)
            continue

        logger.info("Executing tool %s (call=%s session=%s)", name, call_id[:8], session)
        try:
            result: Any = await webbridge.command(name, arguments, session=session)
        except Exception as exc:
            logger.warning("Tool %s failed: %s", name, exc)
            result = {"ok": False, "error": str(exc)}

        api.post_agent_tool_result(task.task_id, call_id=call_id, result=result)
