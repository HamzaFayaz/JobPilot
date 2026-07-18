"""JobPilot Search Helper entry point."""

import asyncio
import logging
import os
import sys

if __name__ == "__main__":
    from worker.runtime_paths import repo_root as _repo_root

    if str(_repo_root()) not in sys.path:
        sys.path.insert(0, str(_repo_root()))

from worker.api_client import JobPilotWorkerClient, RETRYABLE_API_ERRORS
from worker.browser_client import check_browser_health, run_search_task
from worker.cloud_executor import run_cloud_tool_executor
from worker.config import WorkerSettings, get_settings
from worker.models import WorkerTask
from worker.runtime_paths import worker_data_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [Search Helper] %(message)s",
)
# Idle poll hits ECS + WebBridge every few seconds — keep HTTP noise at WARNING.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("worker.main")

_WORKER_LOCK_PATH = worker_data_dir() / ".worker.lock"
_worker_lock_file = None
_IDLE_POLL_LOG_EVERY = 10


def _acquire_single_instance_lock() -> None:
    """Only one worker may poll the API — duplicates steal tasks with no visible logs."""
    global _worker_lock_file
    _WORKER_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    _worker_lock_file = open(_WORKER_LOCK_PATH, "w", encoding="utf-8")
    try:
        if os.name == "nt":
            import msvcrt

            _worker_lock_file.write("0")
            _worker_lock_file.flush()
            msvcrt.locking(_worker_lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(_worker_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        raise SystemExit(
            "Another JobPilot worker is already running on this machine. "
            "Stop the other process before starting a new one — only one worker "
            "should poll the API or tasks/browser activity will not match your terminal."
        ) from exc
    _worker_lock_file.seek(0)
    _worker_lock_file.truncate()
    _worker_lock_file.write(str(os.getpid()))
    _worker_lock_file.flush()
    logger.info("Worker lock acquired (pid=%s)", os.getpid())


def _validate_settings(settings: WorkerSettings) -> None:
    if not settings.worker_token.strip():
        raise SystemExit(
            "WORKER_TOKEN is missing. Pair this computer in JobPilot, then set WORKER_TOKEN in worker/.env"
        )
    mode = (settings.agent_mode or "cloud").strip().lower()
    if mode == "local" and not settings.dashscope_api_key.strip():
        raise SystemExit(
            "DASHSCOPE_API_KEY is missing. Local agent mode needs a Dashscope key in worker/.env "
            "(or set AGENT_MODE=cloud to use the server agent)."
        )


def resolve_agent_mode(task: WorkerTask, settings: WorkerSettings) -> str:
    """Worker AGENT_MODE=local forces the legacy on-PC ReAct path during migration."""
    worker_mode = (settings.agent_mode or "cloud").strip().lower()
    if worker_mode == "local":
        return "local"
    task_mode = (task.agent_mode or "cloud").strip().lower()
    return "local" if task_mode == "local" else "cloud"


async def _run_task(client: JobPilotWorkerClient, settings: WorkerSettings, task) -> None:
    logger.info(
        "Received task %s for run %s (%s / %s)",
        task.task_id,
        task.run_id,
        task.role,
        task.platform,
    )
    mode = resolve_agent_mode(task, settings)
    try:
        client.send_heartbeat(browser_health="busy")
        if mode == "cloud":
            logger.info("Running task %s in cloud agent mode (WebBridge executor)", task.task_id)
            await run_cloud_tool_executor(task, settings, client)
            logger.info("Cloud executor finished task %s", task.task_id)
        else:
            if not settings.dashscope_api_key.strip():
                raise RuntimeError(
                    "Local agent mode requires DASHSCOPE_API_KEY on this Search Helper."
                )
            logger.info("Running task %s in local agent mode (on-PC ReAct)", task.task_id)
            listings, warnings = await run_search_task(task, settings)
            client.post_result(task.task_id, listings, warnings=warnings)
            logger.info("Posted %s listings for task %s", len(listings), task.task_id)
    except Exception as exc:
        logger.exception("Task %s failed", task.task_id)
        try:
            client.post_fail(
                task.task_id,
                error=str(exc),
                code="browser_task_failed",
            )
        except Exception:
            # Cloud agent may already have failed/completed the task.
            logger.exception("Failed to report task failure to JobPilot API")
    finally:
        try:
            client.send_heartbeat(browser_health=check_browser_health(settings))
        except Exception:
            logger.exception("Failed to send ready heartbeat after task")


async def run_forever(settings: WorkerSettings) -> None:
    client = JobPilotWorkerClient(settings)
    logger.info("Connected to JobPilot at %s", settings.jobpilot_api_base)
    logger.info(
        "Browser provider: %s | agent_mode: %s | Qwen model: %s",
        settings.browser_provider,
        settings.agent_mode,
        settings.qwen_model,
    )

    last_health: str | None = None
    idle_polls = 0
    while True:
        try:
            health = check_browser_health(settings)
            client.send_heartbeat(browser_health=health)
            if health != last_health:
                if health == "ready":
                    logger.info("WebBridge ready — Chrome extension connected")
                elif health == "daemon_down":
                    logger.info("WebBridge daemon down — worker will try to restart it")
                elif health == "not_installed":
                    logger.info(
                        "WebBridge daemon running — open Chrome so the extension can connect"
                    )
                else:
                    logger.info("WebBridge status: %s", health)
                last_health = health

            task = client.fetch_next_task()
            if task:
                idle_polls = 0
                if health != "ready":
                    client.post_fail(
                        task.task_id,
                        error=(
                            "Kimi WebBridge is not ready. "
                            "Start the daemon and open Chrome with the extension connected."
                        ),
                        code="browser_not_ready",
                    )
                else:
                    await _run_task(client, settings, task)
            else:
                idle_polls += 1
                if idle_polls == 1 or idle_polls % _IDLE_POLL_LOG_EVERY == 0:
                    logger.info(
                        "Polling for tasks — none pending (pid=%s)",
                        os.getpid(),
                    )
        except Exception as exc:
            if isinstance(exc, RETRYABLE_API_ERRORS):
                logger.warning("Worker loop: ECS unreachable (%s) — will retry", exc)
            else:
                logger.exception("Worker loop error")
            try:
                client.send_heartbeat(browser_health="error")
            except Exception:
                pass

        await asyncio.sleep(settings.poll_interval_seconds)


def main() -> None:
    settings = get_settings()
    _validate_settings(settings)
    _acquire_single_instance_lock()
    logger.info("JobPilot Search Helper starting (poll every %ss)", settings.poll_interval_seconds)
    try:
        asyncio.run(run_forever(settings))
    except KeyboardInterrupt:
        logger.info("Search Helper stopped.")


if __name__ == "__main__":
    main()
