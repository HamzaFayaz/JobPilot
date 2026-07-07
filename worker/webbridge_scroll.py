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
# render before snapshotting or the count reads stale (no new rows).
SCROLL_SETTLE_MS = 1500
# A single no-growth snapshot can just be slow lazy-loading — only give up after
# this many consecutive stalls.
MAX_SCROLL_STALLS = 2


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
