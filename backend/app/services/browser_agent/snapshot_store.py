"""Persist raw WebBridge tool results for offline snapshot analysis."""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Lightweight DOM probe for posts pages — answers "are posts in the DOM even
# when the a11y tree looks empty?" without depending on snapshot shape.
POSTS_DOM_PROBE_JS = """(() => {
  const sel = (s) => document.querySelectorAll(s).length;
  return {
    url: location.href,
    activityUrn: sel('[data-urn*="urn:li:activity"]'),
    feedUpdate: sel('.feed-shared-update-v2, [data-view-name="feed-full-update"]'),
    reusableResult: sel('.reusable-search__result-container'),
    searchResultLi: sel('div.search-results-container li'),
    actor: sel('.update-components-actor'),
    fie: sel('.fie-impression-container')
  };
})()"""


def _run_dir(base_dir: Path, run_id: int) -> Path:
    return base_dir / f"run-{run_id}"


def save_tool_result(
    base_dir: Path,
    *,
    run_id: int,
    phase: str,
    step: int,
    tool_name: str,
    args: dict[str, Any],
    result: Any,
    compressed_result: Any | None = None,
) -> Path | None:
    """Write tool output under run-{id}/{phase}/full/ and optional compressed/."""
    try:
        full_dir = _run_dir(base_dir, run_id) / phase / "full"
        full_dir.mkdir(parents=True, exist_ok=True)
        path = full_dir / f"step-{step:02d}-{tool_name}.json"
        payload = {
            "runId": run_id,
            "phase": phase,
            "step": step,
            "tool": tool_name,
            "args": args,
            "result": result,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved snapshot debug file: %s", path)

        if tool_name == "snapshot" and compressed_result is not None:
            compressed_dir = _run_dir(base_dir, run_id) / phase / "compressed"
            compressed_dir.mkdir(parents=True, exist_ok=True)
            compressed_path = compressed_dir / f"step-{step:02d}-snapshot.json"
            compressed_payload = {
                "runId": run_id,
                "phase": phase,
                "step": step,
                "tool": "snapshot",
                "compressed": compressed_result,
            }
            compressed_path.write_text(
                json.dumps(compressed_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Saved compressed snapshot debug file: %s", compressed_path)

        return path
    except OSError as exc:
        logger.warning("Failed to save snapshot debug file: %s", exc)
        return None


def save_job_enrich_result(
    base_dir: Path,
    *,
    run_id: int,
    job_id: str,
    tool_name: str,
    args: dict[str, Any],
    result: Any,
    compressed_result: Any | None = None,
) -> Path | None:
    """Persist worker-owned job view page captures under jobs/enrich/job-{id}/."""
    try:
        job_dir = _run_dir(base_dir, run_id) / "jobs" / "enrich" / f"job-{job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        path = job_dir / f"{tool_name}.json"
        payload: dict[str, Any] = {
            "runId": run_id,
            "jobId": job_id,
            "tool": tool_name,
            "args": args,
            "result": result,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved job enrich debug file: %s", path)

        if tool_name == "snapshot" and compressed_result is not None:
            compressed_path = job_dir / "snapshot-compressed.json"
            compressed_path.write_text(
                json.dumps(
                    {
                        "runId": run_id,
                        "jobId": job_id,
                        "compressed": compressed_result,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            logger.info("Saved job enrich compressed file: %s", compressed_path)

        return path
    except OSError as exc:
        logger.warning("Failed to save job enrich debug file: %s", exc)
        return None


def _walk_tree(node: Any, visitor) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_tree(item, visitor)
        return
    if not isinstance(node, dict):
        return
    visitor(node)
    children = node.get("children")
    if children is not None:
        _walk_tree(children, visitor)


def diagnose_snapshot_tree(data: dict[str, Any]) -> dict[str, Any]:
    """Summarize a11y tree shape for posts/jobs debugging (local disk only)."""
    # Lazy import to avoid circular imports at module load.
    from backend.app.services.browser_agent.snapshot_compress import (
        _as_feed_post_container,
        _is_feed_post_heading,
        _normalize_snapshot_data,
        count_hiring_openings_in_snapshot,
        extract_posts_from_search_snapshot,
    )

    snapshot = _normalize_snapshot_data(data)
    url = str(snapshot.get("url") or "")
    title = str(snapshot.get("title") or "")
    tree = snapshot.get("tree") or []

    role_counts: Counter[str] = Counter()
    name_samples: list[str] = []
    feed_post_headings = 0
    listitem_feed_posts = 0
    bare_list_bundles = 0
    has_primary_content = False
    filter_button_names: list[str] = []

    def visit(node: dict[str, Any]) -> None:
        nonlocal feed_post_headings, has_primary_content
        role = str(node.get("role") or "")
        name = (node.get("name") or "").strip()
        role_counts[role] += 1
        if _is_feed_post_heading(node):
            feed_post_headings += 1
        if role == "region" and name == "Primary content":
            has_primary_content = True
        if role == "button" and name.lower().startswith("filter"):
            if len(filter_button_names) < 12:
                filter_button_names.append(name[:80])
        if (
            name
            and role in {"heading", "button", "link", "StaticText", "listitem", "region"}
            and len(name_samples) < 30
        ):
            name_samples.append(f"{role}:{name[:80]}")

    _walk_tree(tree, visit)

    def count_shapes(node: Any) -> None:
        nonlocal listitem_feed_posts, bare_list_bundles
        if isinstance(node, list):
            if _as_feed_post_container(node) is not None:
                bare_list_bundles += 1
                return
            for item in node:
                count_shapes(item)
            return
        if not isinstance(node, dict):
            return
        if node.get("role") == "listitem" and _as_feed_post_container(node) is not None:
            listitem_feed_posts += 1
            return
        children = node.get("children")
        if children is not None:
            count_shapes(children)

    count_shapes(tree)

    posts = extract_posts_from_search_snapshot(snapshot)
    hiring = count_hiring_openings_in_snapshot(snapshot)

    if listitem_feed_posts and bare_list_bundles:
        shape = "mixed"
    elif listitem_feed_posts:
        shape = "listitem"
    elif bare_list_bundles:
        shape = "bare_list"
    elif feed_post_headings:
        shape = "orphan_heading"
    else:
        shape = "none"

    return {
        "url": url,
        "title": title,
        "feedPostHeadings": feed_post_headings,
        "feedPostListitems": listitem_feed_posts,
        "feedPostBareBundles": bare_list_bundles,
        "postShape": shape,
        "hasPrimaryContentRegion": has_primary_content,
        "extractedPosts": len(posts),
        "hiringOpenings": hiring,
        "roleCounts": dict(role_counts.most_common(25)),
        "nameSamples": name_samples,
        "filterButtons": filter_button_names,
        "verdict": (
            "posts_extracted"
            if hiring > 0
            else (
                "headings_present_but_parse_failed"
                if feed_post_headings
                else "filters_only_or_empty_tree"
            )
        ),
    }


def save_snapshot_diagnosis(
    base_dir: Path,
    *,
    run_id: int,
    phase: str,
    step: int,
    snapshot: dict[str, Any],
    activity_urls: list[str] | None = None,
    dom_probe: dict[str, Any] | None = None,
) -> Path | None:
    """Write per-step diagnosis JSON under run-{id}/{phase}/diagnosis/."""
    try:
        diagnosis = diagnose_snapshot_tree(snapshot)
        if activity_urls is not None:
            diagnosis["activityUrlCount"] = len(activity_urls)
            diagnosis["activityUrls"] = activity_urls[:20]
        if dom_probe is not None:
            diagnosis["domProbe"] = dom_probe

        out_dir = _run_dir(base_dir, run_id) / phase / "diagnosis"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"step-{step:02d}-snapshot.json"
        payload = {
            "runId": run_id,
            "phase": phase,
            "step": step,
            "diagnosis": diagnosis,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Saved snapshot diagnosis: %s", path)
        return path
    except OSError as exc:
        logger.warning("Failed to save snapshot diagnosis: %s", exc)
        return None
    except Exception as exc:
        logger.warning("Snapshot diagnosis failed: %s", exc)
        return None


def save_scroll_event(
    base_dir: Path,
    *,
    run_id: int,
    phase: str,
    attempt: int,
    before_count: int,
    after_count: int,
    target: int,
    scroll_error: str | None = None,
    step: int | None = None,
) -> Path | None:
    """Append one scroll attempt to run-{id}/{phase}/scrolls.jsonl."""
    try:
        out_dir = _run_dir(base_dir, run_id) / phase
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "scrolls.jsonl"
        record = {
            "runId": run_id,
            "phase": phase,
            "attempt": attempt,
            "before": before_count,
            "after": after_count,
            "target": target,
            "grew": after_count > before_count,
        }
        if step is not None:
            record["step"] = step
        if scroll_error:
            record["error"] = scroll_error
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path
    except OSError as exc:
        logger.warning("Failed to save scroll event: %s", exc)
        return None


def save_activity_urls(
    base_dir: Path,
    *,
    run_id: int,
    phase: str,
    step: int,
    urls: list[str],
    raw_result: Any | None = None,
) -> Path | None:
    """Persist activity-URL evaluate results for a posts snapshot step."""
    try:
        out_dir = _run_dir(base_dir, run_id) / phase / "diagnosis"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"step-{step:02d}-activity-urls.json"
        payload: dict[str, Any] = {
            "runId": run_id,
            "phase": phase,
            "step": step,
            "count": len(urls),
            "urls": urls,
        }
        if raw_result is not None:
            payload["rawResult"] = raw_result
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
    except OSError as exc:
        logger.warning("Failed to save activity URLs: %s", exc)
        return None


def write_run_diagnosis(
    base_dir: Path,
    *,
    run_id: int,
    phase: str | None = None,
) -> Path | None:
    """Aggregate latest per-step diagnoses into diagnosis.json + diagnosis.md."""
    try:
        run_path = _run_dir(base_dir, run_id)
        phases = [phase] if phase else []
        if not phases:
            phases = sorted(
                p.name
                for p in run_path.iterdir()
                if p.is_dir() and (p / "diagnosis").is_dir()
            )

        phase_summaries: list[dict[str, Any]] = []
        for phase_name in phases:
            diag_dir = run_path / phase_name / "diagnosis"
            if not diag_dir.is_dir():
                continue
            steps = sorted(diag_dir.glob("step-*-snapshot.json"))
            if not steps:
                continue
            latest = json.loads(steps[-1].read_text(encoding="utf-8"))
            diagnosis = latest.get("diagnosis") or {}
            scrolls_path = run_path / phase_name / "scrolls.jsonl"
            scroll_attempts = 0
            scroll_grew = 0
            if scrolls_path.is_file():
                lines = [
                    line
                    for line in scrolls_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                scroll_attempts = len(lines)
                for line in lines:
                    try:
                        if json.loads(line).get("grew"):
                            scroll_grew += 1
                    except json.JSONDecodeError:
                        continue
            phase_summaries.append(
                {
                    "phase": phase_name,
                    "stepsDiagnosed": len(steps),
                    "latestStep": latest.get("step"),
                    "url": diagnosis.get("url"),
                    "title": diagnosis.get("title"),
                    "postShape": diagnosis.get("postShape"),
                    "feedPostHeadings": diagnosis.get("feedPostHeadings"),
                    "extractedPosts": diagnosis.get("extractedPosts"),
                    "hiringOpenings": diagnosis.get("hiringOpenings"),
                    "activityUrlCount": diagnosis.get("activityUrlCount"),
                    "domProbe": diagnosis.get("domProbe"),
                    "verdict": diagnosis.get("verdict"),
                    "scrollAttempts": scroll_attempts,
                    "scrollGrew": scroll_grew,
                    "filterButtons": diagnosis.get("filterButtons") or [],
                    "roleCounts": diagnosis.get("roleCounts") or {},
                }
            )

        if not phase_summaries:
            return None

        payload = {"runId": run_id, "phases": phase_summaries}
        json_path = run_path / "diagnosis.json"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = [
            f"# Run {run_id} diagnosis",
            "",
        ]
        for item in phase_summaries:
            lines.extend(
                [
                    f"## Phase: {item['phase']}",
                    f"- URL: `{item.get('url') or ''}`",
                    f"- Title: {item.get('title') or ''}",
                    f"- Post shape: `{item.get('postShape')}`",
                    f"- Feed post headings: {item.get('feedPostHeadings')}",
                    f"- Extracted posts / hiring openings: "
                    f"{item.get('extractedPosts')} / {item.get('hiringOpenings')}",
                    f"- Activity URLs: {item.get('activityUrlCount')}",
                    f"- Scrolls: {item.get('scrollAttempts')} "
                    f"(grew {item.get('scrollGrew')})",
                    f"- Verdict: **{item.get('verdict')}**",
                    "",
                ]
            )
            dom = item.get("domProbe")
            if isinstance(dom, dict):
                lines.append(
                    "- DOM probe: "
                    + ", ".join(f"{k}={v}" for k, v in dom.items() if k != "url")
                )
                lines.append("")
            filters = item.get("filterButtons") or []
            if filters:
                lines.append("- Filter buttons: " + ", ".join(filters[:8]))
                lines.append("")

        md_path = run_path / "diagnosis.md"
        md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        logger.info("Saved run diagnosis: %s", md_path)
        return md_path
    except OSError as exc:
        logger.warning("Failed to write run diagnosis: %s", exc)
        return None
