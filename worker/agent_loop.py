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
    enrich_agent_listings_json,
    merge_listings,
    parse_listings_from_agent_output,
)
from worker.prompts import (
    build_indeed_task,
    build_linkedin_jobs_task,
    build_linkedin_posts_task,
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
from worker.snapshot_compress import compress_snapshot
from worker.snapshot_store import save_tool_result
from worker.webbridge_tools import WEBBRIDGE_TOOL_DEFINITIONS

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
    successful_post_clicks: int,
) -> bool:
    """True when the agent must keep working instead of returning an empty array."""
    if target <= 0 or listings_found > 0:
        return False
    if phase == "posts" and successful_post_clicks == 0 and llm_step < max_steps:
        return True
    return llm_step < min_steps


def _empty_json_nudge(
    *,
    phase: Phase,
    target: int,
    successful_post_clicks: int,
) -> str:
    if phase == "posts" and successful_post_clicks == 0:
        return (
            f"You returned 0 listings but this phase needs up to {target}. "
            "You have not successfully opened a hiring post yet. "
            "Snapshot the results list, click a hiring post from the fresh refs, "
            "snapshot the opened post, extract fields, then return JSON only when done."
        )
    return (
        f"You returned 0 listings but this phase needs up to {target}. "
        "Snapshot the results page, open hiring posts from the list, "
        "and only return JSON when done or no relevant results remain."
    )

_ACTION_LOG_MARKER = "Action log:"
_SNAPSHOT_OMITTED = "[snapshot omitted — see latest]"

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
            + "\n- Snapshot before every click; read description from the snapshot 'About the job' section."
            + "\n- Use evaluate only for window.location.href — not CSS selectors for description."
            + "\n- Job url must be /jobs/view/ and match the list row title/company."
        )
    if phase == "posts":
        return (
            _SYSTEM_PROMPT
            + "\n- This phase is LinkedIn Posts only. Do not return to the Jobs section."
            + "\n- The search page is pre-loaded — do not navigate to the Posts search URL again."
            + "\n- Snapshot before every click; refs go stale after navigation or DOM updates."
            + "\n- Open hiring posts from the list, snapshot the post body, then extract JSON fields."
            + "\n- Post url must be a /feed/update/ or /posts/ activity link — use evaluate for location.href."
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
) -> str:
    try:
        result = await client.command(name, args, session=session)
        compressed_result = None
        llm_payload: Any = result

        if name == "snapshot":
            snapshot_source = result
            if isinstance(result, dict) and isinstance(result.get("data"), dict):
                snapshot_source = result["data"]
            if last_snapshot is not None and isinstance(snapshot_source, dict):
                last_snapshot.clear()
                last_snapshot.append(snapshot_source)
            compressed_result = compress_snapshot(
                snapshot_source if isinstance(snapshot_source, dict) else {}
            )
            llm_payload = _snapshot_llm_payload(result, compressed_result)

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


def _finalize_phase_output(
    *,
    raw_text: str,
    task: WorkerTask,
    phase: Phase,
    last_snapshot_holder: list[dict[str, Any]],
) -> str:
    snapshot = last_snapshot_holder[0] if last_snapshot_holder else None
    return enrich_agent_listings_json(
        raw_text,
        platform=task.platform,
        phase=phase,
        last_snapshot=snapshot,
    )


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
    successful_post_clicks = 0
    bootstrapped = start_url is not None
    last_snapshot_holder: list[dict[str, Any]] = []

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
        )
        _sync_action_log_message(messages, action_log)
        last_tool = "snapshot"

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
                if phase == "posts" and fn_name == "click" and not _tool_result_failed(
                    tool_result
                ):
                    successful_post_clicks += 1
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
                successful_post_clicks=successful_post_clicks,
            ):
                logger.info(
                    "Agent phase=%s rejected early empty JSON at llm_step %s "
                    "(min_steps=%s, post_clicks=%s)",
                    phase,
                    llm_step,
                    min_steps,
                    successful_post_clicks,
                )
                messages.append({"role": "assistant", "content": final_text})
                messages.append(
                    {
                        "role": "user",
                        "content": _empty_json_nudge(
                            phase=phase,
                            target=target,
                            successful_post_clicks=successful_post_clicks,
                        ),
                    }
                )
                continue

            raw_text = _finalize_phase_output(
                raw_text=final_text,
                task=task,
                phase=phase,
                last_snapshot_holder=last_snapshot_holder,
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
    raw_text = _finalize_phase_output(
        raw_text=raw_text,
        task=task,
        phase=phase,
        last_snapshot_holder=last_snapshot_holder,
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
    jobs_target, posts_target = listing_targets(task.max_listings)
    # Testing mode: generous shared cap from agent_max_steps — no tuned per-phase floors.
    phase_max_steps = settings.agent_max_steps

    logger.info(
        "LinkedIn sequential run: jobs_target=%s posts_target=%s phase_max_steps=%s",
        jobs_target,
        posts_target,
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

    if posts_target > 0:
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

    merged = merge_listings(all_listings, max_listings=task.max_listings)
    logger.info("Merged LinkedIn listings: %s (cap %s)", len(merged), task.max_listings)

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
