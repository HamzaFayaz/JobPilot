"""Search execution for the Search Helper — Kimi WebBridge + Qwen ReAct loop."""

from __future__ import annotations

import logging

from worker.agent_loop import run_search_agent
from worker.config import WorkerSettings
from worker.models import RawJobListing, WorkerTask
from worker.parse import parse_listings_from_agent_output
from worker.providers.webbridge import WebBridgeClient

logger = logging.getLogger(__name__)


async def run_search_task(
    task: WorkerTask,
    settings: WorkerSettings,
) -> tuple[list[RawJobListing], list[str]]:
    """Run one browser search and return parsed listings + warnings."""
    warnings: list[str] = []
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
        "Starting WebBridge search: role=%s platform=%s country=%s max=%s age=%s",
        task.role,
        task.platform,
        task.country,
        task.max_listings,
        task.job_age,
    )

    raw_text = await run_search_agent(task, settings, webbridge)
    listings = parse_listings_from_agent_output(raw_text, platform=task.platform)

    if not listings and raw_text.strip():
        warnings.append("browser_parse_partial")
        logger.warning("Agent finished but JSON listings could not be parsed.")

    if len(listings) > task.max_listings:
        listings = listings[: task.max_listings]

    return listings, warnings


def check_browser_health(settings: WorkerSettings) -> str:
    """Return BrowserHealth string for worker heartbeats."""
    if settings.browser_provider != "webbridge":
        return "error"
    return WebBridgeClient(settings.webbridge_url).check_health(auto_start_daemon=True)
