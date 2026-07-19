"""Start the cloud ReAct loop and complete the worker task when finished."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.app.models.browser import RawJobListing as ApiRawJobListing
from backend.app.services.browser_agent.agent_loop import run_search_agent
from backend.app.services.browser_agent.models import WorkerTask
from backend.app.services.browser_agent.parse import parse_listings_from_agent_output
from backend.app.services.browser_agent.remote_browser import RemoteBrowserClient
from backend.app.services.browser_agent.session import (
    BrowserAgentSession,
    drop_session,
)
from backend.app.services.browser_agent.settings import BrowserAgentSettings
from backend.app.services.listing_rewrite import rewrite_listings
from backend.app.services.worker_store import complete_worker_task, fail_worker_task

logger = logging.getLogger(__name__)


async def run_cloud_browser_agent(
    *,
    session: BrowserAgentSession,
    task_payload: dict[str, Any],
) -> None:
    """Async entry used by FastAPI; body runs in a worker thread (sync OpenAI)."""
    await asyncio.to_thread(_run_cloud_browser_agent_sync, session, task_payload)


def _run_cloud_browser_agent_sync(
    session: BrowserAgentSession,
    task_payload: dict[str, Any],
) -> None:
    """Run Qwen ReAct on ECS; tools execute on the worker via WebBridge."""
    task_id = session.task_id
    user_id = session.user_id
    session.status = "running"
    try:
        if not BrowserAgentSettings.from_app_settings().dashscope_api_key.strip():
            raise RuntimeError(
                "DASHSCOPE_API_KEY is not configured on the server for cloud browser agent."
            )

        task = WorkerTask.model_validate(task_payload)
        settings = BrowserAgentSettings.from_app_settings()
        bridge = RemoteBrowserClient(session)

        logger.info(
            "Cloud browser agent starting task=%s run=%s platform=%s",
            task.task_id,
            task.run_id,
            task.platform,
        )
        # agent_loop is async but uses sync OpenAI — dedicated loop on this thread.
        raw_text = asyncio.run(run_search_agent(task, settings, bridge))
        listings = parse_listings_from_agent_output(raw_text, platform=task.platform)
        if len(listings) > task.max_listings:
            listings = listings[: task.max_listings]

        api_listings = [
            ApiRawJobListing.model_validate(item.model_dump(by_alias=True))
            for item in listings
        ]
        rewritten = rewrite_listings(api_listings)
        result_payload = [item.model_dump(by_alias=True) for item in rewritten]
        warnings: list[str] = []
        if not result_payload and raw_text.strip():
            warnings.append("browser_parse_partial")

        if not complete_worker_task(
            task_id,
            user_id=user_id,
            listings=result_payload,
            warnings=warnings,
        ):
            raise RuntimeError("Task is not open for a result")

        logger.info(
            "Cloud browser agent completed task=%s listings=%s",
            task_id,
            len(result_payload),
        )
        session.mark_done()
    except Exception as exc:
        logger.exception("Cloud browser agent failed task=%s", task_id)
        fail_worker_task(
            task_id,
            user_id=user_id,
            error=str(exc),
            code="cloud_agent_failed",
        )
        session.mark_failed(str(exc), code="cloud_agent_failed")
    finally:
        drop_session(task_id)
