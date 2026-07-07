"""Qwen ReAct loop driving Kimi WebBridge tools for job search."""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from openai import OpenAI

from worker.config import WorkerSettings
from worker.linkedin_urls import linkedin_jobs_search_url, linkedin_posts_search_url
from worker.models import RawJobListing, WorkerTask
from worker.parse import (
    current_job_id_from_url,
    enrich_agent_listings_json,
    job_id_from_listing_url,
    linkedin_job_view_url,
    merge_jobs_agent_with_extraction,
    merge_listings,
    merge_posts_agent_with_extraction,
    parse_listings_from_agent_output,
)
from worker.prompts import (
    LINKEDIN_POSTS_PHASE_ENABLED,
    build_indeed_task,
    build_linkedin_jobs_task,
    build_linkedin_posts_task,
    linkedin_jobs_listing_target,
    linkedin_jobs_steps,
    linkedin_posts_steps,
    listing_targets,
)
from worker.providers.webbridge import WebBridgeClient
from worker.run_metrics import (
    LlmCallMetrics,
    PhaseMetrics,
    PhaseRunResult,
    save_run_summary,
)
from worker.snapshot_compress import (
    POST_ACTIVITY_URLS_JS,
    compress_snapshot,
    count_hiring_openings_in_snapshot,
    count_jobs_in_search_snapshot,
    extract_job_description_from_snapshot,
    extract_jobs_from_search_snapshot,
    extract_posts_from_search_snapshot,
    job_detail_metadata,
    snapshot_has_job_detail_panel,
)
from worker.snapshot_store import save_job_enrich_result, save_tool_result
from worker.webbridge_tools import WEBBRIDGE_TOOL_DEFINITIONS
from worker.webbridge_scroll import (
    JOB_DETAIL_WAIT_MS,
    MAX_JOB_DETAIL_RETRIES,
    MAX_JOB_SCROLLS,
    MAX_POST_SCROLLS,
    MAX_SCROLL_STALLS,
    SCROLL_SETTLE_MS,
    enable_foreground_rendering,
    evaluate_job_description,
    scroll_page,
    wait_for_paint,
)

logger = logging.getLogger(__name__)

Phase = Literal["jobs", "posts", "indeed"]


def _min_steps_before_empty_reply(phase: Phase, target: int) -> int:
    if phase == "jobs":
        return linkedin_jobs_steps(target)
    if phase == "posts":
        return linkedin_posts_steps(target)
    return 6


def _tool_result_failed(tool_result: str) -> bool:
    try:
        payload = json.loads(tool_result)
    except json.JSONDecodeError:
        return False
    if not isinstance(payload, dict):
        return False
    if payload.get("ok") is False or payload.get("error"):
        return True
    error = payload.get("error")
    return isinstance(error, dict) and bool(error.get("message"))


def _stale_ref_failure(tool_result: str) -> bool:
    if not _tool_result_failed(tool_result):
        return False
    lowered = tool_result.lower()
    return "does not belong to the document" in lowered or "stale" in lowered


def _reject_empty_json_reply(
    *,
    phase: Phase,
    target: int,
    listings_found: int,
    llm_step: int,
    max_steps: int,
    min_steps: int,
    hiring_openings_visible: int,
) -> bool:
    """True when the agent must keep working instead of returning an empty array."""
    if target <= 0 or listings_found > 0:
        return False
    if phase == "posts" and hiring_openings_visible > 0:
        # Openings are already captured in the snapshot `posts[]`. LinkedIn posts
        # carry no per-post url, so the loop-time parser drops them and the model
        # cannot satisfy a url requirement — but finalize fills these posts via
        # synthetic urls. Accept the reply instead of looping to the step cap;
        # target is a max, and the worker pre-scroll already loaded what exists.
        return False
    return llm_step < min_steps


def _job_detail_not_ready(
    last_snapshot: dict[str, Any] | None,
    *,
    raw_text: str,
    platform: str,
) -> bool:
    if not last_snapshot:
        return False
    url = str(last_snapshot.get("url") or "")
    if not current_job_id_from_url(url):
        return False
    if job_detail_metadata(last_snapshot).get("jobDetailReady"):
        return False
    listings = parse_listings_from_agent_output(raw_text, platform=platform)
    return bool(listings)


def _job_listings_missing_description(
    raw_text: str,
    *,
    platform: str,
    last_snapshot: dict[str, Any] | None,
) -> bool:
    if not last_snapshot:
        return False
    if not snapshot_has_job_detail_panel(last_snapshot):
        return False
    if not extract_job_description_from_snapshot(last_snapshot):
        return False
    listings = parse_listings_from_agent_output(raw_text, platform=platform)
    return any(not item.description_text.strip() for item in listings)


def _reject_incomplete_jobs_reply(
    *,
    phase: Phase,
    target: int,
    listings_found: int,
    llm_step: int,
    max_steps: int,
    job_rows_visible: int,
    raw_text: str,
    platform: str,
    last_snapshot: dict[str, Any] | None,
    accumulated_jobs: dict[str, RawJobListing] | None = None,
    job_descriptions: dict[str, str] | None = None,
) -> bool:
    """True when jobs JSON is incomplete and the agent should keep working."""
    if phase != "jobs" or llm_step >= max_steps or target <= 0:
        return False
    effective_found = listings_found
    if accumulated_jobs is not None:
        effective_found = max(effective_found, len(accumulated_jobs))
    if effective_found < target and job_rows_visible > effective_found:
        return True
    return False


def _accumulated_jobs_missing_description(
    accumulated_jobs: dict[str, RawJobListing],
    job_descriptions: dict[str, str],
) -> bool:
    for job_id, item in accumulated_jobs.items():
        if item.description_text.strip():
            continue
        if not job_descriptions.get(job_id, "").strip():
            return True
    return False


def _job_storage_key(company: str, title: str) -> str:
    """Stable key for accumulated jobs and click-tracked job ids."""
    normalized_title = title.split("|", 1)[0].strip().lower() if title else ""
    return f"{company.strip().lower()}::{normalized_title}"


def _listing_storage_key(
    item: RawJobListing,
    last_snapshot: dict[str, Any] | None,
) -> str:
    if item.company.strip() and item.title.strip():
        return _job_storage_key(item.company, item.title)
    key = job_id_from_listing_url(item.url)
    if key:
        return key
    if last_snapshot:
        snapshot_id = current_job_id_from_url(str(last_snapshot.get("url") or ""))
        if snapshot_id:
            return snapshot_id
    return item.url.strip().lower() or "unknown-job"


def _row_key_from_click_ref(snapshot: dict[str, Any], selector: str) -> str | None:
    """Map a clicked list-row ref to the accumulated_jobs storage key."""
    ref = str(selector or "").strip()
    if ref and not ref.startswith("@"):
        ref = f"@{ref}"
    for row in extract_jobs_from_search_snapshot(snapshot):
        if str(row.get("ref") or "") != ref:
            continue
        parts = [part.strip() for part in str(row.get("name") or "").split("|")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            return _job_storage_key(parts[1], parts[0])
    return None


def _parse_evaluate_href(result: Any) -> str | None:
    if not isinstance(result, dict):
        return None
    data = result.get("data")
    if isinstance(data, dict):
        value = data.get("value")
        if isinstance(value, str) and value.startswith("http"):
            return value
    return None


def _resolve_job_id_for_listing(
    item: RawJobListing,
    *,
    job_ids_by_key: dict[str, str],
) -> str:
    storage_key = _listing_storage_key(item, None)
    return job_ids_by_key.get(storage_key, "") or job_id_from_listing_url(item.url)


def _merge_jobs_into_accumulated(
    accumulated_jobs: dict[str, RawJobListing],
    raw_text: str,
    *,
    platform: str,
    last_snapshot: dict[str, Any] | None,
) -> None:
    for item in parse_listings_from_agent_output(raw_text, platform=platform):
        accumulated_jobs[_listing_storage_key(item, last_snapshot)] = item


def _company_from_job_row_name(name: str) -> str:
    parts = [part.strip() for part in name.split("|")]
    if len(parts) >= 2:
        return parts[1].lower()
    return ""


def _next_job_click_hints(
    last_snapshot: dict[str, Any] | None,
    accumulated_jobs: dict[str, RawJobListing],
    *,
    limit: int = 2,
) -> list[str]:
    if not last_snapshot:
        return []
    collected_companies = {
        item.company.strip().lower() for item in accumulated_jobs.values() if item.company
    }
    hints: list[str] = []
    for row in extract_jobs_from_search_snapshot(last_snapshot):
        company = _company_from_job_row_name(row.get("name", ""))
        if company and company in collected_companies:
            continue
        ref = row.get("ref", "")
        name = row.get("name", "")
        if ref and name:
            hints.append(f"{ref} ({name})")
        if len(hints) >= limit:
            break
    return hints


def _incomplete_jobs_nudge(
    *,
    target: int,
    listings_found: int,
    job_rows_visible: int,
    missing_description: bool,
    job_detail_not_ready: bool,
    accumulated_jobs: dict[str, RawJobListing] | None = None,
    next_refs: list[str] | None = None,
) -> str:
    effective_found = listings_found
    if accumulated_jobs is not None:
        effective_found = max(effective_found, len(accumulated_jobs))
    if job_detail_not_ready:
        return (
            "The job detail panel did not load (jobDetailReady is false). "
            "Click the job card again, wait for the right-rail panel, then snapshot."
        )
    if missing_description:
        return (
            "One or more jobs are missing descriptionText. The worker extracts JD from "
            "the snapshot — ensure the 'About the job' heading is visible, then snapshot again."
        )
    collected = ""
    if accumulated_jobs:
        names = [
            f"{item.title} @ {item.company}".strip()
            for item in accumulated_jobs.values()
        ]
        if names:
            collected = f" Already collected: {', '.join(names)}."
    next_hint = ""
    if next_refs:
        next_hint = f" Next click: {next_refs[0]}."
        if len(next_refs) > 1:
            next_hint += f" Then: {next_refs[1]}."
    elif effective_found < target:
        next_hint = " Pick a different list row you have not collected yet."
    return (
        f"Worker has {effective_found}/{target} job(s); snapshot shows {job_rows_visible} row(s)."
        f"{collected}{next_hint} "
        "Open the next card, evaluate window.location.href for that job's url, "
        "then return JSON with ALL collected jobs in one array."
    )


def _empty_json_nudge(
    *,
    phase: Phase,
    target: int,
    hiring_openings_visible: int,
) -> str:
    if phase == "posts" and hiring_openings_visible > 0:
        return (
            f"You returned 0 listings but the snapshot shows {hiring_openings_visible} "
            f"hiring opening(s). Read fields from the snapshot `posts[]` array — do NOT click posts. "
            f"Return up to {target} openings as JSON, or scroll and snapshot if you need more."
        )
    if phase == "posts":
        return (
            f"You returned 0 listings but this phase needs up to {target}. "
            "Snapshot the results page, read hiring posts from `posts[]`, "
            "scroll with evaluate if needed, then return JSON."
        )
    return (
        f"You returned 0 listings but this phase needs up to {target}. "
        "Snapshot the results page, open hiring posts from the list, "
        "and only return JSON when done or no relevant results remain."
    )

_ACTION_LOG_MARKER = "Action log:"
_SNAPSHOT_OMITTED = "[snapshot omitted — see latest]"
_JOBS_PROGRESS_MARKER = "Jobs progress:"

_SYSTEM_PROMPT = """You are JobPilot Search Helper — a browser agent that searches job sites.

Rules:
- Use WebBridge tools to navigate, read pages (snapshot), click, and fill fields.
- Prefer @e refs from snapshot for click/fill — they survive layout changes.
- Use ONE browser tab for the entire phase — navigate with newTab=false after the first page.
- Follow the user task steps for this phase only.
- When you have enough jobs for this phase, respond with ONLY a JSON array of job objects — no markdown fences.
- Each job object: title, company, url, descriptionText, sourcePlatform.
- If blocked by captcha or login wall, stop and explain briefly in plain text instead of JSON.
"""


def _system_prompt(phase: Phase) -> str:
    if phase == "jobs":
        return (
            _SYSTEM_PROMPT
            + "\n- This phase is LinkedIn Jobs only. Do not search Posts."
            + "\n- Snapshot before every click; collect title, company, and url only."
            + "\n- After you return JSON, the worker visits each job view page to extract the full JD."
            + "\n- Use evaluate only for window.location.href — not CSS selectors for description."
            + "\n- Job url from evaluate may be a search URL with currentJobId — the worker normalizes it."
            + "\n- Return ALL jobs collected so far in every JSON reply — do not re-submit only the latest card."
            + "\n- Job url must match the list row title/company."
        )
    if phase == "posts":
        return (
            _SYSTEM_PROMPT
            + "\n- This phase is LinkedIn Posts only. Do not return to the Jobs section."
            + "\n- The search page is pre-loaded — do not navigate to the Posts search URL again."
            + "\n- Read hiring posts from the snapshot `posts[]` array — do NOT click posts or author links."
            + "\n- `descriptionText` must be the entire post body (apply email, phone, requirements — all visible text)."
            + "\n- Post `url` is optional when contact/apply info is in descriptionText."
            + "\n- The worker may pre-scroll — you do not need to scroll unless asked."
        )
    return _SYSTEM_PROMPT


def _build_client(settings: WorkerSettings) -> OpenAI:
    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
    )


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n…[truncated]"


def _listings_to_json(listings: list[RawJobListing]) -> str:
    return json.dumps(
        [item.model_dump(by_alias=True) for item in listings],
        ensure_ascii=False,
    )


def _message_input_chars(messages: list[dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            total += len(content)
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list):
            for call in tool_calls:
                fn = call.get("function") if isinstance(call, dict) else None
                if isinstance(fn, dict):
                    total += len(str(fn.get("arguments") or ""))
    return total


def _format_action_log(action_log: list[str]) -> str:
    if not action_log:
        return f"{_ACTION_LOG_MARKER}\n(none yet)"
    return _ACTION_LOG_MARKER + "\n" + "\n".join(action_log)


def _sync_action_log_message(messages: list[dict[str, Any]], action_log: list[str]) -> None:
    content = _format_action_log(action_log)
    if (
        len(messages) >= 3
        and messages[2].get("role") == "user"
        and str(messages[2].get("content", "")).startswith(_ACTION_LOG_MARKER)
    ):
        messages[2]["content"] = content
        return
    messages.insert(2, {"role": "user", "content": content})


def _sync_jobs_progress_message(messages: list[dict[str, Any]], content: str) -> None:
    """Replace the jobs progress hint in-place so rejections do not grow token history."""
    full = f"{_JOBS_PROGRESS_MARKER}\n{content}"
    for message in messages:
        if message.get("role") == "user" and str(message.get("content", "")).startswith(
            _JOBS_PROGRESS_MARKER
        ):
            message["content"] = full
            return
    messages.append({"role": "user", "content": full})


def _jobs_phase_raw_text(
    accumulated_jobs: dict[str, RawJobListing],
    *,
    fallback_text: str,
    target: int,
    platform: str,
) -> str:
    if accumulated_jobs:
        jobs = list(accumulated_jobs.values())[:target]
        if jobs:
            return _listings_to_json(jobs)
    parsed = parse_listings_from_agent_output(fallback_text, platform=platform)
    if parsed:
        return _listings_to_json(parsed[:target])
    return fallback_text


def _omit_old_snapshot_messages(
    messages: list[dict[str, Any]],
    snapshot_message_indices: list[int],
    *,
    keep_index: int,
) -> None:
    for idx in snapshot_message_indices:
        if idx == keep_index:
            continue
        if messages[idx].get("role") == "tool":
            messages[idx]["content"] = _SNAPSHOT_OMITTED


def _append_action_log_line(
    action_log: list[str],
    *,
    step: int,
    tool_name: str,
    args: dict[str, Any],
    llm_content: str,
) -> None:
    if tool_name == "navigate":
        url = str(args.get("url", ""))
        action_log.append(f"{step}. navigate → {url} ✓")
        return
    if tool_name == "snapshot":
        try:
            payload = json.loads(llm_content)
            data = payload.get("data", payload)
            node_count = len(data.get("nodes", []))
            action_log.append(f"{step}. snapshot → {node_count} nodes")
        except (json.JSONDecodeError, TypeError, AttributeError):
            action_log.append(f"{step}. snapshot ✓")
        return
    if tool_name == "click":
        ref = args.get("selector") or args.get("ref") or args.get("element") or "element"
        if _tool_result_failed(llm_content):
            action_log.append(f"{step}. click {ref} ✗ stale ref — snapshot again")
        else:
            action_log.append(f"{step}. click {ref} ✓")
        return
    if tool_name == "fill":
        ref = args.get("selector") or args.get("ref") or args.get("element") or "field"
        action_log.append(f"{step}. fill {ref} ✓")
        return
    action_log.append(f"{step}. {tool_name} ✓")


def _short_tool_ack(
    tool_name: str,
    args: dict[str, Any],
    result: Any,
) -> str:
    if isinstance(result, dict) and result.get("error"):
        return json.dumps(result, ensure_ascii=False)
    if tool_name == "navigate":
        url = args.get("url")
        if not url and isinstance(result, dict):
            data = result.get("data")
            if isinstance(data, dict):
                url = data.get("url")
        return json.dumps({"ok": True, "url": url or ""}, ensure_ascii=False)
    return json.dumps({"ok": True}, ensure_ascii=False)


def _snapshot_llm_payload(result: Any, compressed: dict[str, Any]) -> dict[str, Any]:
    if isinstance(result, dict) and "ok" in result:
        return {"ok": result.get("ok", True), "data": compressed}
    return compressed


def _parse_activity_urls(result: Any) -> list[str]:
    if not isinstance(result, dict):
        return []
    data = result.get("data")
    if isinstance(data, dict) and "value" in data:
        value = data.get("value")
    else:
        value = data
    if isinstance(value, list):
        return [str(url).strip() for url in value if str(url).strip()]
    return []


async def _fetch_post_activity_urls(
    client: WebBridgeClient,
    *,
    session: str,
) -> list[str]:
    try:
        result = await client.command(
            "evaluate",
            {"code": POST_ACTIVITY_URLS_JS},
            session=session,
        )
        return _parse_activity_urls(result)
    except Exception as exc:
        logger.warning("Failed to fetch post activity URLs: %s", exc)
        return []


async def _run_tool(
    client: WebBridgeClient,
    name: str,
    args: dict[str, Any],
    *,
    session: str,
    settings: WorkerSettings,
    run_id: int,
    phase: Phase,
    step: int,
    last_snapshot: list[dict[str, Any]] | None = None,
    job_descriptions: dict[str, str] | None = None,
    pending_click_key: list[str | None] | None = None,
    job_ids_by_key: dict[str, str] | None = None,
) -> str:
    try:
        result = await client.command(name, args, session=session)
        compressed_result = None
        llm_payload: Any = result

        if name == "snapshot":
            snapshot_source = result
            if isinstance(result, dict) and isinstance(result.get("data"), dict):
                snapshot_source = result["data"]

            if phase == "jobs" and isinstance(snapshot_source, dict):
                page_url = str(snapshot_source.get("url") or "")
                job_id = current_job_id_from_url(page_url)
                if (
                    job_id
                    and job_descriptions is not None
                    and snapshot_has_job_detail_panel(snapshot_source)
                ):
                    active_job_id = current_job_id_from_url(
                        str(snapshot_source.get("url") or "")
                    )
                    if active_job_id:
                        description = extract_job_description_from_snapshot(snapshot_source)
                        if description:
                            job_descriptions[active_job_id] = description
                if (
                    job_id
                    and job_ids_by_key is not None
                    and pending_click_key is not None
                    and pending_click_key[0]
                ):
                    job_ids_by_key[pending_click_key[0]] = job_id

            if last_snapshot is not None and isinstance(snapshot_source, dict):
                last_snapshot.clear()
                last_snapshot.append(snapshot_source)
            activity_urls: list[str] | None = None
            if phase == "posts":
                activity_urls = await _fetch_post_activity_urls(client, session=session)
            compressed_result = compress_snapshot(
                snapshot_source if isinstance(snapshot_source, dict) else {}
            )
            if phase == "jobs" and isinstance(snapshot_source, dict):
                compressed_result.update(job_detail_metadata(snapshot_source))
            if phase == "posts" and isinstance(compressed_result, dict):
                posts = extract_posts_from_search_snapshot(
                    snapshot_source if isinstance(snapshot_source, dict) else {},
                    activity_urls=activity_urls,
                )
                compressed_result["posts"] = posts
                compressed_result["hiringOpenings"] = sum(
                    1 for post in posts if post.get("isJobOpening")
                )
            llm_payload = _snapshot_llm_payload(result, compressed_result)

        if (
            phase == "jobs"
            and name == "evaluate"
            and job_ids_by_key is not None
            and pending_click_key is not None
            and "location.href" in str(args.get("code") or "")
        ):
            href = _parse_evaluate_href(result)
            storage_key = pending_click_key[0]
            if href and storage_key:
                evaluated_job_id = current_job_id_from_url(href)
                if evaluated_job_id:
                    job_ids_by_key[storage_key] = evaluated_job_id
            pending_click_key[0] = None

        if settings.save_snapshots:
            save_tool_result(
                settings.snapshot_dir,
                run_id=run_id,
                phase=phase,
                step=step,
                tool_name=name,
                args=args,
                result=result,
                compressed_result=compressed_result,
            )

        if name == "snapshot":
            return _truncate(
                json.dumps(llm_payload, ensure_ascii=False),
                settings.snapshot_max_chars,
            )
        return _short_tool_ack(name, args, result)
    except Exception as exc:
        logger.warning("WebBridge tool %s failed: %s", name, exc)
        return json.dumps({"error": str(exc)})


async def _bootstrap_search_page(
    *,
    webbridge: WebBridgeClient,
    settings: WorkerSettings,
    session: str,
    phase: Phase,
    task: WorkerTask,
    start_url: str,
    dedicated_tab: bool,
    action_log: list[str],
    messages: list[dict[str, Any]],
    last_snapshot: list[dict[str, Any]] | None = None,
    job_descriptions: dict[str, str] | None = None,
) -> int:
    """Navigate to pre-built search URL and snapshot before the LLM loop. Returns steps used."""
    nav_args: dict[str, Any] = {
        "url": start_url,
        "group_title": f"JobPilot {phase}",
        "newTab": dedicated_tab,
    }
    logger.info("Bootstrap [%s] navigate → %s", phase, start_url)
    nav_result = await _run_tool(
        webbridge,
        "navigate",
        nav_args,
        session=session,
        settings=settings,
        run_id=task.run_id,
        phase=phase,
        step=1,
    )
    _append_action_log_line(
        action_log,
        step=1,
        tool_name="navigate",
        args=nav_args,
        llm_content=nav_result,
    )

    snap_result = await _run_tool(
        webbridge,
        "snapshot",
        {},
        session=session,
        settings=settings,
        run_id=task.run_id,
        phase=phase,
        step=2,
        last_snapshot=last_snapshot,
        job_descriptions=job_descriptions,
    )
    _append_action_log_line(
        action_log,
        step=2,
        tool_name="snapshot",
        args={},
        llm_content=snap_result,
    )
    messages.append(
        {
            "role": "user",
            "content": (
                "The browser is already on the pre-filtered search results page.\n"
                f"Navigate result: {nav_result}\n"
                f"Initial snapshot:\n{snap_result}"
            ),
        }
    )
    return 2


async def _auto_scroll_after_bootstrap(
    *,
    webbridge: WebBridgeClient,
    settings: WorkerSettings,
    session: str,
    phase: Phase,
    task: WorkerTask,
    target: int,
    start_step: int,
    last_snapshot_holder: list[dict[str, Any]],
    action_log: list[str],
    job_descriptions: dict[str, str] | None = None,
    best_posts_snapshot_holder: list[dict[str, Any]] | None = None,
) -> tuple[int, int]:
    """Worker-owned scroll until target visible or no new content. Returns (attempts, next_step)."""
    if not last_snapshot_holder:
        return 0, start_step

    if phase == "posts":
        count_fn = count_hiring_openings_in_snapshot
        # Scroll budget scales with the target so larger requests can page deeper.
        # Stall detection still stops early when the page runs out of new posts,
        # so a high ceiling never wastes scrolls — it only unlocks depth when
        # there are genuinely more openings to load and we haven't hit target.
        max_scrolls = max(MAX_POST_SCROLLS, target)
        jobs_list = False
    elif phase == "jobs":
        count_fn = count_jobs_in_search_snapshot
        max_scrolls = MAX_JOB_SCROLLS
        jobs_list = True
    else:
        return 0, start_step

    step = start_step
    count = count_fn(last_snapshot_holder[0])
    if count >= target:
        if best_posts_snapshot_holder is not None:
            best_posts_snapshot_holder.clear()
            best_posts_snapshot_holder.append(last_snapshot_holder[0])
        return 0, start_step

    scroll_attempts = 0
    best_count = count
    stall_streak = 0
    if best_posts_snapshot_holder is not None:
        best_posts_snapshot_holder.clear()
        best_posts_snapshot_holder.append(last_snapshot_holder[0])

    # The search tab is opened in the background (newTab); Chrome throttles it and
    # pauses IntersectionObserver, so LinkedIn's infinite scroll never loads past the
    # first screenful. Emulate an active/focused tab so lazy-loading fires, then let it
    # hydrate before the first scroll.
    await enable_foreground_rendering(webbridge, session=session)
    await wait_for_paint(webbridge, session=session, ms=SCROLL_SETTLE_MS)

    while count < target and scroll_attempts < max_scrolls:
        scroll_attempts += 1
        step += 1
        await scroll_page(webbridge, session=session, jobs_list=jobs_list)
        # Give LinkedIn time to fetch and render the newly scrolled-in results
        # before snapshotting — otherwise the count reads stale (no new rows).
        await wait_for_paint(webbridge, session=session, ms=SCROLL_SETTLE_MS)
        step += 1
        snap_result = await _run_tool(
            webbridge,
            "snapshot",
            {},
            session=session,
            settings=settings,
            run_id=task.run_id,
            phase=phase,
            step=step,
            last_snapshot=last_snapshot_holder,
            job_descriptions=job_descriptions,
        )
        _append_action_log_line(
            action_log,
            step=step,
            tool_name="snapshot",
            args={},
            llm_content=snap_result,
        )
        new_count = count_fn(last_snapshot_holder[0])
        action_log.append(f"scroll → {count}→{new_count}")
        logger.info(
            "Worker scroll [%s] attempt %s: %s → %s (target=%s)",
            phase,
            scroll_attempts,
            count,
            new_count,
            target,
        )
        if new_count > count:
            count = new_count
            stall_streak = 0
        else:
            stall_streak += 1
            if stall_streak >= MAX_SCROLL_STALLS:
                break
        if best_posts_snapshot_holder is not None and new_count > best_count:
            best_count = new_count
            best_posts_snapshot_holder.clear()
            best_posts_snapshot_holder.append(last_snapshot_holder[0])

    return scroll_attempts, step


def _snapshot_data_from_result(result: Any) -> dict[str, Any] | None:
    if not isinstance(result, dict):
        return None
    data = result.get("data")
    if isinstance(data, dict) and data.get("tree") is not None:
        return data
    if result.get("tree") is not None:
        return result
    return None


async def _enrich_jobs_from_view_pages(
    *,
    webbridge: WebBridgeClient,
    settings: WorkerSettings,
    session: str,
    task: WorkerTask,
    accumulated_jobs: dict[str, RawJobListing],
    job_descriptions: dict[str, str],
    job_ids_by_key: dict[str, str],
    target: int,
) -> int:
    """Open each job at /jobs/view/{id}/ in a new tab and extract JD text."""
    jobs = list(accumulated_jobs.values())[:target]
    if not jobs:
        return 0

    enriched = 0
    logger.info(
        "Worker job enrich starting: %s job(s) to visit (run_id=%s)",
        len(jobs),
        task.run_id,
    )

    for index, item in enumerate(jobs, start=1):
        job_id = _resolve_job_id_for_listing(item, job_ids_by_key=job_ids_by_key)
        if not job_id:
            logger.warning(
                "Skipping enrich — no job id for %s @ %s",
                item.title,
                item.company,
            )
            continue
        if job_descriptions.get(job_id, "").strip():
            enriched += 1
            continue

        view_url = linkedin_job_view_url(job_id)
        nav_args = {"url": view_url, "newTab": True}
        logger.info(
            "Worker enrich [%s/%s] navigate → %s (%s @ %s)",
            index,
            len(jobs),
            view_url,
            item.title,
            item.company,
        )
        try:
            nav_result = await webbridge.command("navigate", nav_args, session=session)
        except Exception as exc:
            logger.warning("Enrich navigate failed for job %s: %s", job_id, exc)
            continue

        if settings.save_snapshots:
            save_job_enrich_result(
                settings.snapshot_dir,
                run_id=task.run_id,
                job_id=job_id,
                tool_name="navigate",
                args=nav_args,
                result=nav_result,
            )

        snapshot_source: dict[str, Any] | None = None
        snapshot_result: Any = None
        description = ""
        for retry in range(MAX_JOB_DETAIL_RETRIES):
            await wait_for_paint(
                webbridge,
                session=session,
                ms=JOB_DETAIL_WAIT_MS,
            )
            if retry > 0:
                await scroll_page(webbridge, session=session)
                await wait_for_paint(webbridge, session=session, ms=1500)
            try:
                snapshot_result = await webbridge.command("snapshot", {}, session=session)
            except Exception as exc:
                logger.warning("Enrich snapshot failed for job %s: %s", job_id, exc)
                break
            snapshot_source = _snapshot_data_from_result(snapshot_result)
            if snapshot_source:
                description = extract_job_description_from_snapshot(snapshot_source)
            if not description:
                description = await evaluate_job_description(
                    webbridge,
                    session=session,
                )
            if description:
                logger.info(
                    "Job view page ready for %s after %s attempt(s)",
                    job_id,
                    retry + 1,
                )
                break
        else:
            logger.warning(
                "Job view page not ready after %s attempts (jobId=%s)",
                MAX_JOB_DETAIL_RETRIES,
                job_id,
            )

        compressed_result = None
        if snapshot_source:
            compressed_result = compress_snapshot(snapshot_source)
            compressed_result.update(job_detail_metadata(snapshot_source))
            if description:
                compressed_result["jobDetailReady"] = True
                compressed_result["jobDescriptionChars"] = len(description)
            if description:
                job_descriptions[job_id] = description
                enriched += 1
                logger.info(
                    "Extracted %s chars for job %s (%s @ %s)",
                    len(description),
                    job_id,
                    item.title,
                    item.company,
                )

        if settings.save_snapshots and snapshot_result is not None:
            save_job_enrich_result(
                settings.snapshot_dir,
                run_id=task.run_id,
                job_id=job_id,
                tool_name="snapshot",
                args={},
                result=snapshot_result,
                compressed_result=compressed_result,
            )

        try:
            await webbridge.command("close_tab", {}, session=session)
        except Exception as exc:
            logger.debug("Enrich close_tab after job %s: %s", job_id, exc)

    logger.info(
        "Worker job enrich finished: %s/%s with description (run_id=%s)",
        enriched,
        len(jobs),
        task.run_id,
    )
    return enriched


async def _finalize_jobs_phase_output(
    *,
    raw_text: str,
    task: WorkerTask,
    target: int,
    last_snapshot_holder: list[dict[str, Any]],
    accumulated_jobs: dict[str, RawJobListing],
    job_descriptions: dict[str, str],
    job_ids_by_key: dict[str, str],
    webbridge: WebBridgeClient,
    settings: WorkerSettings,
    session: str,
) -> str:
    if accumulated_jobs:
        await _enrich_jobs_from_view_pages(
            webbridge=webbridge,
            settings=settings,
            session=session,
            task=task,
            accumulated_jobs=accumulated_jobs,
            job_descriptions=job_descriptions,
            job_ids_by_key=job_ids_by_key,
            target=target,
        )
    return _finalize_phase_output(
        raw_text=raw_text,
        task=task,
        phase="jobs",
        target=target,
        last_snapshot_holder=last_snapshot_holder,
        job_descriptions=job_descriptions,
    )


def _finalize_phase_output(
    *,
    raw_text: str,
    task: WorkerTask,
    phase: Phase,
    target: int,
    last_snapshot_holder: list[dict[str, Any]],
    best_posts_snapshot_holder: list[dict[str, Any]] | None = None,
    job_descriptions: dict[str, str] | None = None,
) -> str:
    snapshot = last_snapshot_holder[0] if last_snapshot_holder else None
    if phase == "posts":
        posts_snapshot = (
            best_posts_snapshot_holder[0]
            if best_posts_snapshot_holder
            else snapshot
        )
        raw_text = merge_posts_agent_with_extraction(
            raw_text,
            platform=task.platform,
            last_snapshot=posts_snapshot,
            target=target,
        )
    elif phase == "jobs" and job_descriptions:
        raw_text = merge_jobs_agent_with_extraction(
            raw_text,
            platform=task.platform,
            job_descriptions=job_descriptions,
            last_snapshot=snapshot,
        )

    text = enrich_agent_listings_json(
        raw_text,
        platform=task.platform,
        phase=phase,
        last_snapshot=snapshot,
        job_descriptions=job_descriptions if phase == "jobs" else None,
    )
    return text


async def _run_agent_phase(
    *,
    task: WorkerTask,
    settings: WorkerSettings,
    webbridge: WebBridgeClient,
    session: str,
    phase: Phase,
    user_task: str,
    target: int,
    max_steps: int,
    dedicated_tab: bool = False,
    start_url: str | None = None,
) -> PhaseRunResult:
    """One ReAct loop with compressed snapshots, telemetry, and no hard failure on cap."""
    metrics = PhaseMetrics(
        phase=phase,
        target=target,
        max_steps=max_steps,
        steps_used=0,
        stop_reason="skipped",
        listings_found=0,
        session=session,
    )

    if max_steps <= 0 or target <= 0:
        metrics.stop_reason = "skipped"
        return PhaseRunResult(raw_text="[]", metrics=metrics)

    llm = _build_client(settings)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _system_prompt(phase)},
        {"role": "user", "content": user_task},
    ]
    action_log: list[str] = []
    snapshot_message_indices: list[int] = []
    first_navigate = start_url is None
    last_tool: str | None = None
    raw_text = "[]"
    bootstrap_steps = 0
    bootstrapped = start_url is not None
    last_snapshot_holder: list[dict[str, Any]] = []
    best_posts_snapshot_holder: list[dict[str, Any]] = []
    job_descriptions: dict[str, str] = {}
    accumulated_jobs: dict[str, RawJobListing] = {}
    job_ids_by_key: dict[str, str] = {}
    pending_click_key: list[str | None] = [None]
    last_hiring_openings = 0
    last_job_rows = 0
    bootstrap_step = 0
    last_rejected_jobs_json = ""
    repeat_incomplete_jobs_json = 0

    logger.info(
        "Starting agent phase=%s max_steps=%s session=%s run_id=%s",
        phase,
        max_steps,
        session,
        task.run_id,
    )

    if start_url:
        bootstrap_steps = await _bootstrap_search_page(
            webbridge=webbridge,
            settings=settings,
            session=session,
            phase=phase,
            task=task,
            start_url=start_url,
            dedicated_tab=dedicated_tab,
            action_log=action_log,
            messages=messages,
            last_snapshot=last_snapshot_holder,
            job_descriptions=job_descriptions,
        )
        _sync_action_log_message(messages, action_log)
        last_tool = "snapshot"
        bootstrap_step = bootstrap_steps
        if phase == "jobs" and last_snapshot_holder:
            last_job_rows = count_jobs_in_search_snapshot(last_snapshot_holder[0])
        if phase == "posts" and last_snapshot_holder:
            last_hiring_openings = count_hiring_openings_in_snapshot(
                last_snapshot_holder[0]
            )
            best_posts_snapshot_holder.clear()
            best_posts_snapshot_holder.append(last_snapshot_holder[0])

        scroll_attempts, bootstrap_step = await _auto_scroll_after_bootstrap(
            webbridge=webbridge,
            settings=settings,
            session=session,
            phase=phase,
            task=task,
            target=target,
            start_step=bootstrap_steps,
            last_snapshot_holder=last_snapshot_holder,
            action_log=action_log,
            job_descriptions=job_descriptions,
            best_posts_snapshot_holder=(
                best_posts_snapshot_holder if phase == "posts" else None
            ),
        )
        if scroll_attempts:
            _sync_action_log_message(messages, action_log)
            if phase == "posts" and last_snapshot_holder:
                last_hiring_openings = count_hiring_openings_in_snapshot(
                    last_snapshot_holder[0]
                )
            elif phase == "jobs" and last_snapshot_holder:
                last_job_rows = count_jobs_in_search_snapshot(last_snapshot_holder[0])
            compressed = compress_snapshot(last_snapshot_holder[0])
            if phase == "posts":
                posts = extract_posts_from_search_snapshot(last_snapshot_holder[0])
                compressed["posts"] = posts
                compressed["hiringOpenings"] = sum(
                    1 for post in posts if post.get("isJobOpening")
                )
            elif phase == "jobs":
                compressed.update(job_detail_metadata(last_snapshot_holder[0]))
            snap_preview = _truncate(
                json.dumps({"ok": True, "data": compressed}, ensure_ascii=False),
                settings.snapshot_max_chars,
            )
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Worker pre-scrolled {scroll_attempts} time(s) to load more results.\n"
                        f"Latest snapshot:\n{snap_preview}"
                    ),
                }
            )
        if phase == "jobs":
            metrics.scroll_attempts_jobs = scroll_attempts
        elif phase == "posts":
            metrics.scroll_attempts_posts = scroll_attempts
        bootstrap_steps = bootstrap_step

    for step in range(max_steps):
        metrics.steps_used = bootstrap_steps + step + 1
        _sync_action_log_message(messages, action_log)
        input_chars = _message_input_chars(messages)
        completion = llm.chat.completions.create(
            model=settings.qwen_model,
            temperature=0.2,
            messages=messages,
            tools=WEBBRIDGE_TOOL_DEFINITIONS,
            tool_choice="auto",
        )
        choice = completion.choices[0].message
        usage = completion.usage
        tool_names = [call.function.name for call in (choice.tool_calls or [])]
        metrics.add_llm_call(
            LlmCallMetrics(
                step=step + 1,
                prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
                total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
                input_chars=input_chars,
                tools=tool_names,
            )
        )
        logger.info(
            "LLM [%s] step %s tokens in=%s out=%s total=%s chars=%s tools=%s",
            phase,
            step + 1,
            metrics.llm_calls[-1].prompt_tokens,
            metrics.llm_calls[-1].completion_tokens,
            metrics.llm_calls[-1].total_tokens,
            input_chars,
            tool_names or "(reply)",
        )

        if choice.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": choice.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in choice.tool_calls
                    ],
                }
            )
            for call in choice.tool_calls:
                fn_name = call.function.name
                last_tool = fn_name
                try:
                    fn_args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    fn_args = {}
                if not isinstance(fn_args, dict):
                    fn_args = {}

                if fn_name == "navigate":
                    fn_args.setdefault("group_title", f"JobPilot {phase}")
                    if dedicated_tab and first_navigate:
                        fn_args.setdefault("newTab", True)
                        first_navigate = False
                    else:
                        fn_args.setdefault("newTab", False)
                    if (
                        phase == "posts"
                        and bootstrapped
                        and "/search/results/content/" in str(fn_args.get("url", ""))
                    ):
                        tool_result = json.dumps(
                            {
                                "ok": False,
                                "error": (
                                    "Already on the Posts search page from bootstrap. "
                                    "Do not navigate to the search URL again — snapshot "
                                    "and click hiring posts from the current list."
                                ),
                            },
                            ensure_ascii=False,
                        )
                        _append_action_log_line(
                            action_log,
                            step=step + 1,
                            tool_name=fn_name,
                            args=fn_args,
                            llm_content=tool_result,
                        )
                        _sync_action_log_message(messages, action_log)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call.id,
                                "content": tool_result,
                            }
                        )
                        continue

                if phase == "posts" and fn_name == "click":
                    tool_result = json.dumps(
                        {
                            "ok": False,
                            "error": (
                                "Do not click posts on the search page — read hiring "
                                "openings from the snapshot posts[] array instead."
                            ),
                        },
                        ensure_ascii=False,
                    )
                    _append_action_log_line(
                        action_log,
                        step=step + 1,
                        tool_name=fn_name,
                        args=fn_args,
                        llm_content=tool_result,
                    )
                    _sync_action_log_message(messages, action_log)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": tool_result,
                        }
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Stay on the search page. Snapshot if needed, then copy "
                                "fields from posts[] where isJobOpening is true."
                            ),
                        }
                    )
                    continue

                if phase == "jobs" and fn_name == "click" and last_snapshot_holder:
                    pending_click_key[0] = _row_key_from_click_ref(
                        last_snapshot_holder[0],
                        str(fn_args.get("selector") or fn_args.get("ref") or ""),
                    )

                logger.info(
                    "WebBridge [%s] step %s: %s %s",
                    phase,
                    step + 1,
                    fn_name,
                    list(fn_args.keys()),
                )
                tool_result = await _run_tool(
                    webbridge,
                    fn_name,
                    fn_args,
                    session=session,
                    settings=settings,
                    run_id=task.run_id,
                    phase=phase,
                    step=bootstrap_steps + step + 1,
                    last_snapshot=last_snapshot_holder,
                    job_descriptions=job_descriptions,
                    pending_click_key=pending_click_key if phase == "jobs" else None,
                    job_ids_by_key=job_ids_by_key if phase == "jobs" else None,
                )
                _append_action_log_line(
                    action_log,
                    step=step + 1,
                    tool_name=fn_name,
                    args=fn_args,
                    llm_content=tool_result,
                )
                _sync_action_log_message(messages, action_log)

                tool_message_index = len(messages)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": tool_result,
                    }
                )
                if fn_name == "snapshot":
                    _omit_old_snapshot_messages(
                        messages,
                        snapshot_message_indices,
                        keep_index=tool_message_index,
                    )
                    snapshot_message_indices.append(tool_message_index)
                    try:
                        payload = json.loads(tool_result)
                        data = payload.get("data", payload)
                        if isinstance(data, dict):
                            last_hiring_openings = int(data.get("hiringOpenings") or 0)
                            if phase == "jobs" and last_snapshot_holder:
                                last_job_rows = count_jobs_in_search_snapshot(
                                    last_snapshot_holder[0]
                                )
                    except (json.JSONDecodeError, TypeError, ValueError):
                        pass
                if fn_name == "click" and _stale_ref_failure(tool_result):
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "That click ref is stale. Snapshot the page now and "
                                "use only @e refs from the new snapshot before clicking."
                            ),
                        }
                    )
            continue

        final_text = (choice.content or "").strip()
        if final_text:
            listings_found = len(
                parse_listings_from_agent_output(raw_text := final_text, platform=task.platform)
            )
            llm_step = step + 1
            min_steps = _min_steps_before_empty_reply(phase, target)
            if _reject_empty_json_reply(
                phase=phase,
                target=target,
                listings_found=listings_found,
                llm_step=llm_step,
                max_steps=max_steps,
                min_steps=min_steps,
                hiring_openings_visible=last_hiring_openings,
            ):
                logger.info(
                    "Agent phase=%s rejected early empty JSON at llm_step %s "
                    "(min_steps=%s, hiring_openings=%s)",
                    phase,
                    llm_step,
                    min_steps,
                    last_hiring_openings,
                )
                messages.append({"role": "assistant", "content": final_text})
                messages.append(
                    {
                        "role": "user",
                        "content": _empty_json_nudge(
                            phase=phase,
                            target=target,
                            hiring_openings_visible=last_hiring_openings,
                        ),
                    }
                )
                continue

            snapshot = last_snapshot_holder[0] if last_snapshot_holder else None
            if phase == "jobs":
                _merge_jobs_into_accumulated(
                    accumulated_jobs,
                    final_text,
                    platform=task.platform,
                    last_snapshot=snapshot,
                )
            effective_listings_found = len(accumulated_jobs) if phase == "jobs" else listings_found
            if _reject_incomplete_jobs_reply(
                phase=phase,
                target=target,
                listings_found=listings_found,
                llm_step=llm_step,
                max_steps=max_steps,
                job_rows_visible=last_job_rows,
                raw_text=final_text,
                platform=task.platform,
                last_snapshot=snapshot,
                accumulated_jobs=accumulated_jobs if phase == "jobs" else None,
                job_descriptions=job_descriptions if phase == "jobs" else None,
            ):
                logger.info(
                    "Agent phase=%s rejected incomplete jobs JSON at llm_step %s "
                    "(found=%s, target=%s, job_rows=%s, accumulated=%s)",
                    phase,
                    llm_step,
                    listings_found,
                    target,
                    last_job_rows,
                    effective_listings_found,
                )
                if phase == "jobs":
                    if final_text == last_rejected_jobs_json:
                        repeat_incomplete_jobs_json += 1
                    else:
                        last_rejected_jobs_json = final_text
                        repeat_incomplete_jobs_json = 1
                    next_refs = _next_job_click_hints(snapshot, accumulated_jobs)
                    nudge = _incomplete_jobs_nudge(
                        target=target,
                        listings_found=listings_found,
                        job_rows_visible=last_job_rows,
                        missing_description=False,
                        job_detail_not_ready=False,
                        accumulated_jobs=accumulated_jobs,
                        next_refs=next_refs,
                    )
                    messages.append({"role": "assistant", "content": final_text})
                    _sync_jobs_progress_message(messages, nudge)
                    if repeat_incomplete_jobs_json >= 2 and next_refs:
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "You returned the same incomplete JSON without using tools. "
                                    f"Do NOT reply with JSON yet — call click on {next_refs[0]}, "
                                    "evaluate window.location.href for the url, "
                                    "then return JSON with all collected jobs."
                                ),
                            }
                        )
                continue

            phase_raw_text = (
                _jobs_phase_raw_text(
                    accumulated_jobs,
                    fallback_text=final_text,
                    target=target,
                    platform=task.platform,
                )
                if phase == "jobs"
                else final_text
            )
            if phase == "jobs":
                raw_text = await _finalize_jobs_phase_output(
                    raw_text=phase_raw_text,
                    task=task,
                    target=target,
                    last_snapshot_holder=last_snapshot_holder,
                    accumulated_jobs=accumulated_jobs,
                    job_descriptions=job_descriptions,
                    job_ids_by_key=job_ids_by_key,
                    webbridge=webbridge,
                    settings=settings,
                    session=session,
                )
            else:
                raw_text = _finalize_phase_output(
                    raw_text=phase_raw_text,
                    task=task,
                    phase=phase,
                    target=target,
                    last_snapshot_holder=last_snapshot_holder,
                    best_posts_snapshot_holder=(
                        best_posts_snapshot_holder if phase == "posts" else None
                    ),
                    job_descriptions=None,
                )
            metrics.stop_reason = "completed_json"
            metrics.last_tool = last_tool
            metrics.listings_found = len(
                parse_listings_from_agent_output(raw_text, platform=task.platform)
            )
            logger.info(
                "Agent phase=%s finished after %s steps (%s listings, %s total tokens)",
                phase,
                step + 1,
                metrics.listings_found,
                metrics.total_tokens,
            )
            return PhaseRunResult(raw_text=raw_text, metrics=metrics)

        messages.append({"role": "assistant", "content": ""})
        messages.append(
            {
                "role": "user",
                "content": "Continue with tools or return the final JSON array of jobs.",
            }
        )

    metrics.stop_reason = "exceeded_max_steps"
    metrics.last_tool = last_tool
    raw_text = _jobs_phase_raw_text(
        accumulated_jobs,
        fallback_text=raw_text,
        target=target,
        platform=task.platform,
    ) if phase == "jobs" else raw_text
    if phase == "jobs":
        raw_text = await _finalize_jobs_phase_output(
            raw_text=raw_text,
            task=task,
            target=target,
            last_snapshot_holder=last_snapshot_holder,
            accumulated_jobs=accumulated_jobs,
            job_descriptions=job_descriptions,
            webbridge=webbridge,
            settings=settings,
            session=session,
        )
    else:
        raw_text = _finalize_phase_output(
            raw_text=raw_text,
            task=task,
            phase=phase,
            target=target,
            last_snapshot_holder=last_snapshot_holder,
            best_posts_snapshot_holder=(
                best_posts_snapshot_holder if phase == "posts" else None
            ),
            job_descriptions=None,
        )
    metrics.listings_found = len(
        parse_listings_from_agent_output(raw_text, platform=task.platform)
    )
    logger.warning(
        "Agent phase=%s hit step cap %s (last_tool=%s, %s total tokens) — returning partial",
        phase,
        max_steps,
        last_tool,
        metrics.total_tokens,
    )
    return PhaseRunResult(raw_text=raw_text, metrics=metrics)


async def _run_linkedin_search(
    task: WorkerTask,
    settings: WorkerSettings,
    webbridge: WebBridgeClient,
) -> str:
    jobs_target = linkedin_jobs_listing_target(task.max_listings)
    posts_target = 0
    if LINKEDIN_POSTS_PHASE_ENABLED:
        _, posts_target = listing_targets(task.max_listings)
    # Testing mode: generous shared cap from agent_max_steps — no tuned per-phase floors.
    phase_max_steps = settings.agent_max_steps

    logger.info(
        "LinkedIn sequential run: jobs_target=%s posts_target=%s posts_enabled=%s phase_max_steps=%s",
        jobs_target,
        posts_target,
        LINKEDIN_POSTS_PHASE_ENABLED,
        phase_max_steps,
    )

    jobs_session = f"jobpilot-run-{task.run_id}-jobs"
    posts_session = f"jobpilot-run-{task.run_id}-posts"

    phase_results: list[PhaseRunResult] = []

    if jobs_target > 0:
        logger.info("LinkedIn phase starting: jobs")
        phase_results.append(
            await _run_agent_phase(
                task=task,
                settings=settings,
                webbridge=webbridge,
                session=jobs_session,
                phase="jobs",
                user_task=build_linkedin_jobs_task(task, target=jobs_target),
                target=jobs_target,
                max_steps=phase_max_steps,
                dedicated_tab=True,
                start_url=linkedin_jobs_search_url(task),
            )
        )

    if posts_target > 0 and LINKEDIN_POSTS_PHASE_ENABLED:
        logger.info("LinkedIn phase starting: posts")
        phase_results.append(
            await _run_agent_phase(
                task=task,
                settings=settings,
                webbridge=webbridge,
                session=posts_session,
                phase="posts",
                user_task=build_linkedin_posts_task(task, target=posts_target),
                target=posts_target,
                max_steps=phase_max_steps,
                dedicated_tab=True,
                start_url=linkedin_posts_search_url(task),
            )
        )

    all_listings: list[RawJobListing] = []
    phase_metrics: list[PhaseMetrics] = []
    for result in phase_results:
        phase_metrics.append(result.metrics)
        listings = parse_listings_from_agent_output(
            result.raw_text, platform=task.platform
        )
        logger.info(
            "Phase %s: %s listings, %s steps, stop=%s, tokens=%s",
            result.metrics.phase,
            len(listings),
            result.metrics.steps_used,
            result.metrics.stop_reason,
            result.metrics.total_tokens,
        )
        all_listings.extend(listings)

    merged = merge_listings(all_listings, max_listings=jobs_target if not LINKEDIN_POSTS_PHASE_ENABLED else task.max_listings)
    cap = jobs_target if not LINKEDIN_POSTS_PHASE_ENABLED else task.max_listings
    logger.info("Merged LinkedIn listings: %s (cap %s)", len(merged), cap)

    save_run_summary(
        settings.snapshot_dir,
        run_id=task.run_id,
        max_listings=task.max_listings,
        role=task.role,
        platform=task.platform,
        country=task.country,
        phases=phase_metrics,
        merged_listings=len(merged),
        parallel=False,
    )

    return _listings_to_json(merged)


async def run_search_agent(
    task: WorkerTask,
    settings: WorkerSettings,
    webbridge: WebBridgeClient,
) -> str:
    """Run Qwen + WebBridge; LinkedIn runs Jobs then Posts sequentially."""
    if task.platform == "linkedin":
        return await _run_linkedin_search(task, settings, webbridge)

    session = f"jobpilot-run-{task.run_id}"
    result = await _run_agent_phase(
        task=task,
        settings=settings,
        webbridge=webbridge,
        session=session,
        phase="indeed",
        user_task=build_indeed_task(task),
        target=task.max_listings,
        max_steps=settings.agent_max_steps,
    )
    save_run_summary(
        settings.snapshot_dir,
        run_id=task.run_id,
        max_listings=task.max_listings,
        role=task.role,
        platform=task.platform,
        country=task.country,
        phases=[result.metrics],
        merged_listings=result.metrics.listings_found,
        parallel=False,
    )
    return result.raw_text
