"""Browser-Use search execution for the Search Helper."""

import logging
import os
from pathlib import Path

from browser_use import Agent, BrowserProfile, BrowserSession, ChatOpenAI
from browser_use.browser.profile import BrowserChannel

from worker.config import WorkerSettings
from worker.models import RawJobListing, WorkerTask
from worker.parse import parse_listings_from_agent_output
from worker.prompts import build_search_task

logger = logging.getLogger(__name__)


def _chrome_user_data_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        return Path(local_app_data) / "Google" / "Chrome" / "User Data"
    return Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"


def _build_llm(settings: WorkerSettings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.qwen_model,
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
    )


def _build_browser_profile(task: WorkerTask, settings: WorkerSettings) -> BrowserProfile:
    # Local worker/.env wins — ECS does not know this PC's Chrome profile layout.
    profile_dir = settings.browser_chrome_profile or task.chrome_profile_directory
    logger.info("Using Chrome profile directory: %s", profile_dir)
    return BrowserProfile(
        channel=BrowserChannel.CHROME,
        user_data_dir=_chrome_user_data_dir(),
        profile_directory=profile_dir,
        headless=False,
    )


async def run_search_task(
    task: WorkerTask,
    settings: WorkerSettings,
) -> tuple[list[RawJobListing], list[str]]:
    """Run one browser search and return parsed listings + warnings."""
    warnings: list[str] = []
    browser_profile = _build_browser_profile(task, settings)
    browser_session = BrowserSession(browser_profile=browser_profile)
    llm = _build_llm(settings)
    prompt = build_search_task(task)

    logger.info(
        "Starting browser search: role=%s platform=%s country=%s max=%s age=%s",
        task.role,
        task.platform,
        task.country,
        task.max_listings,
        task.job_age,
    )

    agent = Agent(
        task=prompt,
        llm=llm,
        browser_session=browser_session,
        use_vision=False,
        max_actions_per_step=1,
    )

    try:
        history = await agent.run()
        raw_text = history.final_result() or ""
        listings = parse_listings_from_agent_output(raw_text, platform=task.platform)

        if not listings and raw_text.strip():
            warnings.append("browser_parse_partial")
            logger.warning("Agent finished but JSON listings could not be parsed.")

        if len(listings) > task.max_listings:
            listings = listings[: task.max_listings]

        return listings, warnings
    finally:
        try:
            await browser_session.stop()
        except Exception:
            logger.exception("Failed to close browser session cleanly")
