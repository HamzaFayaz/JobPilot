"""Worker-owned page scrolling via Kimi WebBridge evaluate."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from worker.providers.webbridge import WebBridgeClient

logger = logging.getLogger(__name__)

SCROLL_PAGE_JS = "window.scrollBy(0, window.innerHeight)"
SCROLL_JOBS_LIST_JS = (
    "(() => { const list = document.querySelector("
    "'.jobs-search-results-list, .scaffold-layout__list'); "
    "if (list) { list.scrollBy(0, list.clientHeight); return 'list'; } "
    "window.scrollBy(0, window.innerHeight); return 'window'; })()"
)
WAIT_PAINT_JS = "await new Promise(r => setTimeout(r, 1500))"

MAX_POST_SCROLLS = 5
MAX_JOB_SCROLLS = 3
MAX_JOB_DETAIL_RETRIES = 3


async def scroll_page(
    client: WebBridgeClient,
    *,
    session: str,
    jobs_list: bool = False,
) -> None:
    code = SCROLL_JOBS_LIST_JS if jobs_list else SCROLL_PAGE_JS
    await client.command("evaluate", {"code": code}, session=session)


async def wait_for_paint(
    client: WebBridgeClient,
    *,
    session: str,
    ms: int = 1500,
) -> None:
    await client.command(
        "evaluate",
        {"code": f"await new Promise(r => setTimeout(r, {ms}))"},
        session=session,
    )


async def scroll_until_count(
    client: WebBridgeClient,
    *,
    session: str,
    target: int,
    max_scrolls: int,
    count_fn: Callable[[dict[str, Any]], int],
    take_snapshot: Callable[[], Awaitable[dict[str, Any]]],
    jobs_list: bool = False,
    on_scroll: Callable[[int, int, int], None] | None = None,
) -> tuple[dict[str, Any] | None, int, int]:
    """Scroll until count reaches target or no new content. Returns best snapshot, best count, attempts."""
    snapshot = await take_snapshot()
    best_snapshot = snapshot
    count = count_fn(snapshot)
    best_count = count
    scroll_attempts = 0

    while count < target and scroll_attempts < max_scrolls:
        scroll_attempts += 1
        await scroll_page(client, session=session, jobs_list=jobs_list)
        snapshot = await take_snapshot()
        new_count = count_fn(snapshot)
        if on_scroll:
            on_scroll(scroll_attempts, count, new_count)
        logger.info(
            "Worker scroll attempt %s: count %s → %s (target=%s)",
            scroll_attempts,
            count,
            new_count,
            target,
        )
        if new_count <= count:
            break
        count = new_count
        if new_count > best_count:
            best_count = new_count
            best_snapshot = snapshot

    return best_snapshot, best_count, scroll_attempts
