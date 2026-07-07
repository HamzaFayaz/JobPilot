"""Throwaway diagnostic: run post-extraction against saved snapshots."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from worker.snapshot_compress import (
    _collect_feed_post_listitems,
    _parse_feed_post_listitem,
    _flatten_nodes,
    _has_hiring_intent,
    _is_job_opening_post,
    extract_posts_from_search_snapshot,
    count_hiring_openings_in_snapshot,
)

BASE = Path(__file__).resolve().parent / "debug_snapshots" / "run-62" / "posts" / "full"


def load(step: str) -> dict:
    raw = json.loads((BASE / step).read_text(encoding="utf-8"))
    return raw["result"]["data"]


def diag(step: str) -> None:
    data = load(step)
    print(f"\n===== {step} =====")
    print("url:", data.get("url", "")[:90])

    listitems: list[dict] = []
    _collect_feed_post_listitems(data.get("tree") or [], listitems)
    print(f"feed-post listitems collected: {len(listitems)}")

    posts = extract_posts_from_search_snapshot(data)
    print(f"posts extracted: {len(posts)}")
    print(f"hiring openings: {count_hiring_openings_in_snapshot(data)}")

    for i, li in enumerate(listitems):
        parsed = _parse_feed_post_listitem(li)
        if parsed is None:
            # figure out why
            nodes = list(_flatten_nodes(li))
            body_texts = []
            for node in nodes:
                role = node.get("role") or ""
                name = (node.get("name") or "").strip()
                if role == "StaticText" and name and name != "Feed post" and len(name) >= 8:
                    body_texts.append(name)
            combined = " ".join(body_texts)
            reason = "no body_texts" if not body_texts else (
                "no hiring intent" if not _has_hiring_intent(combined) else "unknown"
            )
            print(f"  [{i}] DROPPED ({reason}) — sample: {combined[:120]!r}")
        else:
            print(
                f"  [{i}] KEPT isJobOpening={parsed['isJobOpening']} "
                f"author={parsed['author']!r} title={parsed['title'][:60]!r}"
            )


for step in ("step-02-snapshot.json", "step-04-snapshot.json", "step-08-snapshot.json"):
    diag(step)
