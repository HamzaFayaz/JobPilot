"""JobPilot Search Helper entry point."""

import asyncio
import logging
import sys
from pathlib import Path

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from worker.api_client import JobPilotWorkerClient
from worker.browser_client import run_search_task
from worker.config import WorkerSettings, get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [Search Helper] %(message)s",
)
logger = logging.getLogger("worker.main")


def _validate_settings(settings: WorkerSettings) -> None:
    if not settings.worker_token.strip():
        raise SystemExit(
            "WORKER_TOKEN is missing. Pair this computer in JobPilot, then set WORKER_TOKEN in worker/.env"
        )
    if not settings.dashscope_api_key.strip():
        raise SystemExit(
            "DASHSCOPE_API_KEY is missing. Add your Dashscope key to worker/.env for browser search."
        )


async def _run_task(client: JobPilotWorkerClient, settings: WorkerSettings, task) -> None:
    logger.info(
        "Received task %s for run %s (%s / %s)",
        task.task_id,
        task.run_id,
        task.role,
        task.platform,
    )
    try:
        client.send_heartbeat(browser_health="busy")
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
            logger.exception("Failed to report task failure to JobPilot API")
    finally:
        try:
            client.send_heartbeat(browser_health="ready")
        except Exception:
            logger.exception("Failed to send ready heartbeat after task")


async def run_forever(settings: WorkerSettings) -> None:
    client = JobPilotWorkerClient(settings)
    logger.info("Connected to JobPilot at %s", settings.jobpilot_api_base)
    logger.info("Using Qwen model: %s", settings.qwen_model)

    while True:
        try:
            client.send_heartbeat(browser_health="ready")
            task = client.fetch_next_task()
            if task:
                await _run_task(client, settings, task)
            else:
                logger.debug("No pending tasks")
        except Exception:
            logger.exception("Worker loop error")
            try:
                client.send_heartbeat(browser_health="error")
            except Exception:
                pass

        await asyncio.sleep(settings.poll_interval_seconds)


def main() -> None:
    settings = get_settings()
    _validate_settings(settings)
    logger.info("JobPilot Search Helper starting (poll every %ss)", settings.poll_interval_seconds)
    try:
        asyncio.run(run_forever(settings))
    except KeyboardInterrupt:
        logger.info("Search Helper stopped.")


if __name__ == "__main__":
    main()
