"""Worker-owned page scrolling via Kimi WebBridge evaluate."""

from __future__ import annotations

import asyncio
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

# Kimi WebBridge evaluate scripts — no external scrapers. Structure-based:
# h2 "About the job" then paragraph siblings (matches LinkedIn job view layout).

JOB_SCROLL_TO_DESCRIPTION_JS = """(() => {
  const isAbout = (el) => /^about the job$/i.test((el.innerText || '').trim());
  const about = [...document.querySelectorAll('h2, [role="heading"]')].find(isAbout);
  if (about) about.scrollIntoView({ block: 'start', behavior: 'instant' });
  return Boolean(about);
})()"""

JOB_EXPAND_DESCRIPTION_JS = """(() => {
  const isAbout = (el) => /^about the job$/i.test((el.innerText || '').trim());
  const about = [...document.querySelectorAll('h2, [role="heading"]')].find(isAbout);
  if (!about) return false;
  let el = about;
  for (let i = 0; i < 40; i++) {
    el = el.nextElementSibling;
    if (!el) break;
    for (const btn of el.querySelectorAll('button, [role="button"]')) {
      const label = ((btn.getAttribute('aria-label') || '') + ' ' + (btn.innerText || '')).toLowerCase();
      if (/(see more|show more|…more|\\.\\.\\.more)/i.test(label)) {
        btn.click();
        return true;
      }
    }
    const own = (el.innerText || '').toLowerCase();
    if (/(see more|show more|…more|\\.\\.\\.more)/i.test(own) && el.click) {
      el.click();
      return true;
    }
  }
  return false;
})()"""

JOB_DESCRIPTION_EXTRACT_JS = """(() => {
  const isAbout = (el) => /^about the job$/i.test((el.innerText || '').trim());
  const about = [...document.querySelectorAll('h2, [role="heading"]')].find(isAbout);
  if (!about) return '';
  const parts = [];
  let el = about.nextElementSibling;
  for (let i = 0; i < 50 && el; i++) {
    const tag = (el.tagName || '').toLowerCase();
    if ((tag === 'h2' || tag === 'h3') && !isAbout(el)) break;
    const text = (el.innerText || '').trim();
    if (text.length > 30 && !isAbout(el)) parts.push(text);
    el = el.nextElementSibling;
  }
  return parts.join('\\n\\n').trim();
})()"""

MAX_POST_SCROLLS = 5
MAX_JOB_SCROLLS = 3
MAX_JOB_DETAIL_RETRIES = 8
JOB_DETAIL_WAIT_MS = 3000
# LinkedIn lazy-loads results over the network after a scroll; wait for them to
# render before snapshotting or the count reads stale (no new rows). Loading can
# lag 1-2s+, so keep this generous — a short wait makes results nondeterministic.
SCROLL_SETTLE_MS = 2000
# A no-growth snapshot is often just slow lazy-loading, not the end of results
# (observed: the same query returned 5 openings on one run and gave up at 2 on
# another). Tolerate several stalls before quitting so laggy posts get caught.
MAX_SCROLL_STALLS = 3


# A search tab opened with newTab (in the background) is throttled by Chrome:
# JS timers are slowed and IntersectionObserver is paused, so LinkedIn's
# infinite scroll never fires and results stay stuck at the first screenful.
# Emulating an active/focused tab via CDP re-enables lazy-loading without having
# to steal the user's foreground tab. See job-section-issue.md for the same root
# cause on the Jobs enrich path.
FOREGROUND_CDP_COMMANDS: tuple[tuple[str, dict[str, Any]], ...] = (
    ("Page.enable", {}),
    ("Page.setWebLifecycleState", {"state": "active"}),
    ("Emulation.setFocusEmulationEnabled", {"enabled": True}),
)


async def enable_foreground_rendering(
    client: WebBridgeClient,
    *,
    session: str,
) -> None:
    """Make a background tab report as visible/focused so lazy-loaded content renders."""
    for method, params in FOREGROUND_CDP_COMMANDS:
        try:
            await client.command(
                "cdp", {"method": method, "params": params}, session=session
            )
        except Exception as exc:
            logger.warning("Foreground CDP %s failed: %s", method, exc)


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
    # Pause the worker (not the page) so lazy-loaded content has real wall-clock
    # time to arrive before the next snapshot. A browser-side setTimeout via
    # `evaluate` is NOT reliably awaited by the daemon (it returns immediately,
    # observed as sub-second scroll intervals), so the wait must happen here.
    # The browser keeps fetching/rendering during this sleep.
    del client, session  # kept for call-site compatibility; wait is worker-side
    await asyncio.sleep(ms / 1000)


async def evaluate_job_description(
    client: WebBridgeClient,
    *,
    session: str,
) -> str:
    """Read JD via WebBridge evaluate: scroll to h2 About the job, expand, read paragraphs."""
    try:
        await client.command(
            "evaluate",
            {"code": JOB_SCROLL_TO_DESCRIPTION_JS},
            session=session,
        )
        await wait_for_paint(client, session=session, ms=800)
        await client.command(
            "evaluate",
            {"code": JOB_EXPAND_DESCRIPTION_JS},
            session=session,
        )
        await wait_for_paint(client, session=session, ms=600)
        result = await client.command(
            "evaluate",
            {"code": JOB_DESCRIPTION_EXTRACT_JS},
            session=session,
        )
    except Exception as exc:
        logger.warning("Job description evaluate failed: %s", exc)
        return ""
    if not isinstance(result, dict):
        return ""
    data = result.get("data")
    if isinstance(data, dict):
        value = data.get("value")
        if isinstance(value, str) and len(value.strip()) >= 100:
            return value.strip()
    return ""


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
