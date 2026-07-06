"""Semantic compression of WebBridge accessibility-tree snapshots for LLM context."""

from __future__ import annotations

import re
from typing import Any

_DROP_NAME_SUBSTRINGS = (
    "new notification",
    "notification",
    "close jump menu",
    "messaging",
    "for business",
    "hire with ai",
    "post impressions",
    "premium",
    "boost your job",
)

_KEEP_INPUT_ROLES = frozenset({"textbox", "searchbox", "combobox"})

_FILTER_PHRASES = (
    "filter",
    "show all filters",
    "show results",
    "reset applied",
    "date posted filter",
    "experience level filter",
    "company filter",
    "remote filter",
    "filter by:",
    "past week",
    "past 24 hours",
    "past month",
)

_SKIP_JOB_ROW_STATIC = frozenset(
    {
        "viewed",
        "easy apply",
        "actively hiring",
        "be an early applicant",
    }
)

_EXCLUDED_TITLE_PREFIXES = (
    "dismiss",
    "apply to",
    "view ",
    "linkedin",
    "sign in",
)

_NOTIFICATION_HEADING = re.compile(r"^\d+\s+notifications?$", re.IGNORECASE)
_JOBS_SEARCH_TITLE = re.compile(r"\(\d+\).+jobs in", re.IGNORECASE)
_AUTHOR_CONNECTION = re.compile(r"(?:•\s*)?(1st|2nd|3rd)\s*$", re.IGNORECASE)

_HIRING_SNIPPET_KEYWORDS = (
    "hiring",
    "we're hiring",
    "we are hiring",
    "looking for",
    "#hiring",
    "is hiring",
    "open role",
    "job opening",
    "we're looking",
)

_POSTS_FILTER_PHRASES = _FILTER_PHRASES + (
    "filter by posts",
    "filter by top match",
    "filter by past week",
    "filter by content type",
    "filter by from member",
    "all filters",
)


def _normalize_snapshot_data(data: dict[str, Any]) -> dict[str, Any]:
    """Accept raw WebBridge envelope or bare {url, title, tree}."""
    if "tree" in data:
        return data
    inner = data.get("data")
    if isinstance(inner, dict) and "tree" in inner:
        return inner
    return data


def _is_jobs_search_page(url: str, title: str) -> bool:
    if "/jobs/search" in (url or "").lower():
        return True
    return bool(_JOBS_SEARCH_TITLE.search(title or ""))


def _is_posts_search_page(url: str) -> bool:
    return "/search/results/content" in (url or "").lower()


def _has_hiring_intent(text: str) -> bool:
    lower = text.lower()
    return any(keyword in lower for keyword in _HIRING_SNIPPET_KEYWORDS)


def _truncate_snippet(text: str, *, max_len: int = 100) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned
    trimmed = cleaned[: max_len - 1].rsplit(" ", 1)[0]
    return f"{trimmed}…"


def _iter_child_nodes(children: Any) -> list[Any]:
    if children is None:
        return []
    if isinstance(children, list):
        return children
    return [children]


def _flatten_nodes(node: Any):
    if isinstance(node, list):
        for item in node:
            yield from _flatten_nodes(item)
        return
    if not isinstance(node, dict):
        return
    yield node
    for child in _iter_child_nodes(node.get("children")):
        yield from _flatten_nodes(child)


def _first_static_text_name(node: dict[str, Any]) -> str:
    for child in _iter_child_nodes(node.get("children")):
        if not isinstance(child, dict):
            continue
        if child.get("role") == "StaticText":
            name = (child.get("name") or "").strip()
            if name:
                return name
        nested = _first_static_text_name(child)
        if nested:
            return nested
    return ""


def _effective_name(node: dict[str, Any]) -> str:
    name = (node.get("name") or "").strip()
    if name:
        return name
    return _first_static_text_name(node)


def _is_excluded_job_title_link(name: str) -> bool:
    lower = name.lower()
    return any(lower.startswith(prefix) for prefix in _EXCLUDED_TITLE_PREFIXES)


def _is_job_card(role: str, name: str) -> bool:
    if role != "link":
        return False
    if "•" not in name:
        return False
    lower = name.lower()
    return "posted" in lower or "easy apply" in lower or " job" in lower


def _is_nav_jobs_or_search(role: str, name: str) -> bool:
    if role not in {"link", "button"}:
        return False
    lower = name.lower()
    return lower.startswith("jobs") or lower.startswith("search")


def _is_filter_control(role: str, name: str, *, posts_page: bool = False) -> bool:
    if role != "button":
        return False
    lower = name.lower()
    phrases = _POSTS_FILTER_PHRASES if posts_page else _FILTER_PHRASES
    return any(phrase in lower for phrase in phrases)


def _should_keep_node(
    role: str,
    name: str,
    *,
    posts_page: bool = False,
) -> bool:
    if role in _KEEP_INPUT_ROLES:
        return True
    if posts_page and _is_nav_jobs_or_search(role, name):
        return False
    if _is_nav_jobs_or_search(role, name):
        return True
    if _is_filter_control(role, name, posts_page=posts_page):
        return True
    if _is_job_card(role, name):
        return True
    return False


def _should_drop_node(role: str, name: str) -> bool:
    if role == "heading" and _NOTIFICATION_HEADING.match(name.strip()):
        return True
    if _is_job_card(role, name) or _is_nav_jobs_or_search(role, name):
        return False
    if role == "button" and name.lower().startswith("dismiss"):
        return True
    lower = name.lower()
    return any(token in lower for token in _DROP_NAME_SUBSTRINGS)


def _try_extract_post_search_row(listitem: dict[str, Any]) -> dict[str, str] | None:
    """One posts search result: author link + hiring snippet."""
    nodes = list(_flatten_nodes(listitem))
    if not any(
        node.get("role") == "heading" and (node.get("name") or "").strip() == "Feed post"
        for node in nodes
    ):
        return None

    author_name = ""
    author_ref: str | None = None
    timestamp_ref: str | None = None
    body_texts: list[str] = []

    for node in nodes:
        role = node.get("role") or ""
        name = (node.get("name") or "").strip()
        ref = node.get("ref")

        if role == "link" and ref and name and _AUTHOR_CONNECTION.search(name):
            author_ref = str(ref)
            author_name = name.split("•", 1)[0].strip()
            timestamp_ref = None
        elif role == "link" and ref and not name and author_ref:
            timestamp_ref = str(ref)
        elif role == "StaticText" and name:
            if name == "Feed post":
                continue
            if _AUTHOR_CONNECTION.search(name):
                continue
            if len(name) < 20:
                continue
            if name.endswith("•") or name.endswith("• "):
                continue
            if name not in body_texts:
                body_texts.append(name)

    if not author_ref or not author_name or not body_texts:
        return None

    combined = " ".join(body_texts)
    if not _has_hiring_intent(combined):
        return None

    snippet = next((text for text in body_texts if _has_hiring_intent(text)), body_texts[0])
    click_ref = timestamp_ref or author_ref
    return {
        "ref": click_ref,
        "role": "link",
        "name": f"{author_name} | {_truncate_snippet(snippet)}",
    }


def _collect_posts_search_results(
    node: Any,
    nodes: list[dict[str, str]],
    seen_refs: set[str],
) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_posts_search_results(item, nodes, seen_refs)
        return
    if not isinstance(node, dict):
        return

    if node.get("role") == "listitem":
        row = _try_extract_post_search_row(node)
        if row and row["ref"] not in seen_refs:
            nodes.append(row)
            seen_refs.add(row["ref"])

    for child in _iter_child_nodes(node.get("children")):
        _collect_posts_search_results(child, nodes, seen_refs)


def _try_extract_job_search_row(listitem: dict[str, Any]) -> dict[str, str] | None:
    """One left-rail search result: title link + company + location."""
    has_dismiss = False
    title_ref: str | None = None
    title_name = ""
    static_texts: list[str] = []

    for node in _flatten_nodes(listitem):
        role = node.get("role") or ""
        name = (node.get("name") or "").strip()
        if not name:
            continue
        if role == "button" and "dismiss" in name.lower() and " job" in name.lower():
            has_dismiss = True
        elif role == "link" and node.get("ref") and title_ref is None:
            if not _is_excluded_job_title_link(name):
                title_ref = str(node["ref"])
                title_name = name
        elif role == "StaticText":
            if name.lower() not in _SKIP_JOB_ROW_STATIC:
                static_texts.append(name)

    if not has_dismiss or not title_ref or not title_name:
        return None

    extras: list[str] = []
    for text in static_texts:
        if text.lower() == title_name.lower():
            continue
        if text not in extras:
            extras.append(text)

    parts = [title_name]
    if extras:
        parts.append(extras[0])
    if len(extras) > 1:
        parts.append(extras[1])

    return {"ref": title_ref, "role": "link", "name": " | ".join(parts)}


def _collect_jobs_search_results(
    node: Any,
    nodes: list[dict[str, str]],
    seen_refs: set[str],
) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_jobs_search_results(item, nodes, seen_refs)
        return
    if not isinstance(node, dict):
        return

    if node.get("role") == "listitem":
        row = _try_extract_job_search_row(node)
        if row and row["ref"] not in seen_refs:
            nodes.append(row)
            seen_refs.add(row["ref"])

    for child in _iter_child_nodes(node.get("children")):
        _collect_jobs_search_results(child, nodes, seen_refs)


def _walk_tree(
    node: Any,
    nodes: list[dict[str, str]],
    *,
    seen_refs: set[str],
    posts_page: bool = False,
    in_complementary: bool = False,
) -> None:
    if isinstance(node, list):
        for item in node:
            _walk_tree(
                item,
                nodes,
                seen_refs=seen_refs,
                posts_page=posts_page,
                in_complementary=in_complementary,
            )
        return

    if not isinstance(node, dict):
        return

    role = node.get("role") or ""
    if role == "complementary":
        return

    if in_complementary:
        return

    if role == "InlineTextBox":
        return

    name = _effective_name(node)
    ref = node.get("ref")

    if ref and str(ref) in seen_refs:
        return

    if ref and _should_keep_node(role, name, posts_page=posts_page) and not _should_drop_node(
        role, name
    ):
        nodes.append({"ref": str(ref), "role": role, "name": name})
        return

    for child in _iter_child_nodes(node.get("children")):
        _walk_tree(
            child,
            nodes,
            seen_refs=seen_refs,
            posts_page=posts_page,
            in_complementary=in_complementary,
        )


def compress_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    """Compress WebBridge snapshot to slim nodes for LLM context.

    Input: {url, title, tree} or WebBridge {ok, data: {url, title, tree}}.
    Output: {url, title, nodes: [{ref, role, name}]}.
    """
    snapshot = _normalize_snapshot_data(data)
    url = str(snapshot.get("url") or "")
    title = str(snapshot.get("title") or "")
    tree = snapshot.get("tree") or []
    nodes: list[dict[str, str]] = []
    seen_refs: set[str] = set()
    posts_page = _is_posts_search_page(url)

    if _is_jobs_search_page(url, title):
        _collect_jobs_search_results(tree, nodes, seen_refs)

    if posts_page:
        _collect_posts_search_results(tree, nodes, seen_refs)

    _walk_tree(tree, nodes, seen_refs=seen_refs, posts_page=posts_page)
    return {
        "url": url,
        "title": title,
        "nodes": nodes,
    }


def extract_job_description_from_snapshot(data: dict[str, Any], *, max_chars: int = 4000) -> str:
    """Read job description text from the right-rail 'About the job' section."""
    snapshot = _normalize_snapshot_data(data)
    tree = snapshot.get("tree") or []
    texts: list[str] = []
    capture = False

    for node in _flatten_nodes(tree):
        role = node.get("role") or ""
        name = (node.get("name") or "").strip()
        if role == "heading" and name.lower() == "about the job":
            capture = True
            continue
        if not capture:
            continue
        if role == "heading" and name.lower() != "about the job":
            break
        if role == "StaticText" and len(name) > 25:
            if name not in texts:
                texts.append(name)

    description = " ".join(texts).strip()
    if len(description) > max_chars:
        description = description[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return description
