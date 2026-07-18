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

_SKIP_POST_LINK_NAMES = frozenset(
    {
        "send",
        "like",
        "comment",
        "repost",
        "open reactions menu",
        "view job",
    }
)

_POST_TIMESTAMP = re.compile(r"^\d+[hdwm]\s*•", re.IGNORECASE)
_DEBATE_PHRASES = (
    "a question to",
    "let's discuss",
    "what do you think",
    "industry, software houses",
)
_JOB_OPENING_PHRASES = (
    "we're hiring",
    "we are hiring",
    "position:",
    "apply today",
    "send your resume",
    "send their resume",
    "interested candidates",
    "open role",
    "view job",
)

POST_DESCRIPTION_MAX_CHARS = 12000
JOB_DESCRIPTION_MAX_CHARS = 12000

POST_ACTIVITY_URLS_JS = """(() => {
  const urls = [];
  const roots = document.querySelectorAll('[data-urn*="urn:li:activity"]');
  roots.forEach(el => {
    const a = el.querySelector('a[href*="/feed/update/"], a[href*="/posts/"]');
    if (a && a.href) urls.push(a.href);
  });
  return urls;
})()"""


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


def _is_job_opening_post(combined: str) -> bool:
    lower = combined.lower()
    if any(phrase in lower for phrase in _DEBATE_PHRASES):
        if not any(phrase in lower for phrase in _JOB_OPENING_PHRASES):
            return False
    return _has_hiring_intent(lower)


def _is_feed_post_heading(node: dict[str, Any]) -> bool:
    return (
        node.get("role") == "heading"
        and (node.get("name") or "").strip() == "Feed post"
    )


def _list_contains_top_level_feed_post_heading(items: list[Any]) -> bool:
    """True when a bare list bundle starts with / contains a top-level Feed post heading.

    Newer WebBridge a11y trees expose posts as flat lists under Primary content
    (not wrapped in role=listitem). Older trees keep the listitem wrapper.
    """
    for item in items:
        if isinstance(item, dict) and _is_feed_post_heading(item):
            return True
    return False


def _as_feed_post_container(node: Any) -> dict[str, Any] | None:
    """Normalize listitem or bare list bundle into a dict for parsing."""
    if isinstance(node, dict) and node.get("role") == "listitem":
        flat = list(_flatten_nodes(node))
        if any(_is_feed_post_heading(item) for item in flat):
            return node
        return None
    if isinstance(node, list) and _list_contains_top_level_feed_post_heading(node):
        return {"role": "listitem", "children": node}
    return None


def _collect_feed_post_listitems(node: Any, out: list[dict[str, Any]]) -> None:
    if isinstance(node, list):
        # Prefer treating the whole list as one post bundle when it looks like
        # the new WebBridge shape — avoid double-counting nested fragments.
        container = _as_feed_post_container(node)
        if container is not None:
            out.append(container)
            return
        for item in node:
            _collect_feed_post_listitems(item, out)
        return
    if not isinstance(node, dict):
        return
    container = _as_feed_post_container(node)
    if container is not None:
        out.append(container)
        return
    for child in _iter_child_nodes(node.get("children")):
        _collect_feed_post_listitems(child, out)


def _extract_post_author(nodes: list[dict[str, Any]]) -> tuple[str, str]:
    author = ""
    headline = ""
    for node in nodes:
        role = node.get("role") or ""
        name = (node.get("name") or "").strip()
        if role != "link" or not name:
            continue
        if _AUTHOR_CONNECTION.search(name):
            author = name.split("•", 1)[0].strip()
            continue
        if not author and 1 < len(name) < 80 and "notification" not in name.lower():
            author = name
            continue
        if author and not headline and len(name) > 25 and name != author:
            headline = name
    return author, headline


def _extract_post_title(body_texts: list[str]) -> str:
    for text in body_texts:
        if re.search(r"we['']re hiring|we are hiring", text, re.IGNORECASE):
            return text.split(".")[0].strip()[:200]
    for text in body_texts:
        match = re.search(r"💼\s*Position:\s*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:200]
    for text in body_texts:
        if "#hiring" in text.lower() and len(text) > 25:
            return text[:200]
    return body_texts[0][:200] if body_texts else "Hiring post"


def _extract_post_company(author: str, body_texts: list[str]) -> str:
    for text in body_texts:
        match = re.match(
            r"^([A-Za-z0-9][\w\s&'.-]{1,50})\s+is\s+(looking|hiring)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
    if author:
        return author.split("•", 1)[0].strip()
    return "Unknown"


def _extract_post_location(body_texts: list[str]) -> str:
    for text in body_texts:
        match = re.search(r"📍\s*Location:\s*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    for text in body_texts:
        if "|" in text and re.search(r"\(.*\)", text):
            return text.split("|")[-1].strip()[:120]
    return ""


def _parse_feed_post_listitem(listitem: dict[str, Any]) -> dict[str, Any] | None:
    nodes = list(_flatten_nodes(listitem))
    author, author_headline = _extract_post_author(nodes)
    posted_ago = ""
    body_texts: list[str] = []

    for node in nodes:
        role = node.get("role") or ""
        name = (node.get("name") or "").strip()
        if role == "link" and name:
            lower = name.lower()
            if lower in _SKIP_POST_LINK_NAMES:
                continue
            if name not in body_texts:
                body_texts.append(name)
            continue
        if role != "StaticText" or not name:
            continue
        if name == "Feed post":
            continue
        if _AUTHOR_CONNECTION.search(name):
            continue
        if _POST_TIMESTAMP.match(name):
            posted_ago = name.replace("•", "").strip()
            continue
        if len(name) < 8:
            continue
        if name.endswith("•") or name.endswith("• "):
            continue
        if name == author or name == author_headline:
            continue
        if name not in body_texts:
            body_texts.append(name)

    if not body_texts:
        return None

    combined = " ".join(body_texts)
    if not _has_hiring_intent(combined):
        return None

    title = _extract_post_title(body_texts)
    company = _extract_post_company(author, body_texts)
    location = _extract_post_location(body_texts)
    description = " ".join(body_texts).strip()
    if len(description) > POST_DESCRIPTION_MAX_CHARS:
        description = (
            description[: POST_DESCRIPTION_MAX_CHARS - 1].rsplit(" ", 1)[0] + "…"
        )

    return {
        "author": author,
        "authorHeadline": author_headline,
        "postedAgo": posted_ago,
        "title": title,
        "company": company,
        "location": location,
        "descriptionText": description,
        "isJobOpening": _is_job_opening_post(combined),
        "url": "",
    }


def extract_posts_from_search_snapshot(
    data: dict[str, Any],
    *,
    activity_urls: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Structured hiring posts from the posts search listing page (no clicks)."""
    snapshot = _normalize_snapshot_data(data)
    url = str(snapshot.get("url") or "")
    if not _is_posts_search_page(url):
        return []

    listitems: list[dict[str, Any]] = []
    _collect_feed_post_listitems(snapshot.get("tree") or [], listitems)

    posts: list[dict[str, Any]] = []
    for listitem in listitems:
        parsed = _parse_feed_post_listitem(listitem)
        if parsed:
            posts.append(parsed)

    if activity_urls:
        for index, post in enumerate(posts):
            if index < len(activity_urls) and activity_urls[index]:
                post["url"] = activity_urls[index]

    return posts


def count_hiring_openings_in_snapshot(data: dict[str, Any]) -> int:
    return sum(
        1 for post in extract_posts_from_search_snapshot(data) if post.get("isJobOpening")
    )


def extract_jobs_from_search_snapshot(data: dict[str, Any]) -> list[dict[str, str]]:
    """Left-rail job result rows on a Jobs search page (ref + display name)."""
    snapshot = _normalize_snapshot_data(data)
    url = str(snapshot.get("url") or "")
    title = str(snapshot.get("title") or "")
    if not _is_jobs_search_page(url, title):
        return []
    nodes: list[dict[str, str]] = []
    seen_refs: set[str] = set()
    _collect_jobs_search_results(snapshot.get("tree") or [], nodes, seen_refs)
    return nodes


def count_jobs_in_search_snapshot(data: dict[str, Any]) -> int:
    """Count left-rail job result rows on a Jobs search page."""
    return len(extract_jobs_from_search_snapshot(data))


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
        extracted_posts = extract_posts_from_search_snapshot(snapshot)
    else:
        extracted_posts = []

    _walk_tree(tree, nodes, seen_refs=seen_refs, posts_page=posts_page)
    result: dict[str, Any] = {
        "url": url,
        "title": title,
        "nodes": nodes,
    }
    if posts_page:
        result["posts"] = extracted_posts
        result["hiringOpenings"] = sum(
            1 for post in extracted_posts if post.get("isJobOpening")
        )
    return result


def snapshot_has_job_detail_panel(data: dict[str, Any]) -> bool:
    """True when accessibility tree contains an 'About the job' heading."""
    snapshot = _normalize_snapshot_data(data)
    for node in _flatten_nodes(snapshot.get("tree") or []):
        role = node.get("role") or ""
        name = (node.get("name") or "").strip()
        if role == "heading" and name.lower() == "about the job":
            return True
    return False


def job_detail_metadata(data: dict[str, Any]) -> dict[str, bool | int]:
    """LLM-facing metadata only — not the full job description body."""
    ready = snapshot_has_job_detail_panel(data)
    chars = (
        len(extract_job_description_from_snapshot(data, max_chars=JOB_DESCRIPTION_MAX_CHARS))
        if ready
        else 0
    )
    return {"jobDetailReady": ready, "jobDescriptionChars": chars}


def _static_texts_from_node(node: dict[str, Any], *, min_len: int = 25) -> list[str]:
    texts: list[str] = []
    for child in _flatten_nodes(node):
        if child.get("role") != "StaticText":
            continue
        name = (child.get("name") or "").strip()
        if len(name) >= min_len and name not in texts:
            texts.append(name)
    return texts


def extract_job_description_from_snapshot(
    data: dict[str, Any], *, max_chars: int = JOB_DESCRIPTION_MAX_CHARS
) -> str:
    """Read JD from WebBridge snapshot: heading 'About the job' then paragraph text."""
    snapshot = _normalize_snapshot_data(data)
    tree = snapshot.get("tree") or []
    texts: list[str] = []
    capture = False
    nodes = list(_flatten_nodes(tree))

    for node in nodes:
        role = node.get("role") or ""
        name = (node.get("name") or "").strip()
        if role == "heading" and name.lower() == "about the job":
            capture = True
            continue
        if not capture:
            continue
        if role == "heading" and name.lower() != "about the job":
            break
        if role == "paragraph":
            for chunk in _static_texts_from_node(node):
                if chunk not in texts:
                    texts.append(chunk)
        elif role == "StaticText" and len(name) > 25:
            if name not in texts:
                texts.append(name)

    description = " ".join(texts).strip()
    if len(description) > max_chars:
        description = description[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return description
