"""Tests for worker-owned scroll stop conditions."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from worker.webbridge_scroll import (
    SCROLL_PAGE_JS,
    scroll_page,
    scroll_until_count,
)

RUN40_POSTS_COMPRESSED = (
    Path(__file__).resolve().parents[1]
    / "worker"
    / "debug_snapshots"
    / "run-40"
    / "posts"
    / "compressed"
    / "step-02-snapshot.json"
)


def _load_posts_fixture() -> dict:
    payload = json.loads(RUN40_POSTS_COMPRESSED.read_text(encoding="utf-8"))
    return payload["compressed"]


@pytest.mark.asyncio
async def test_scroll_page_calls_evaluate_with_scroll_js():
    client = AsyncMock()
    await scroll_page(client, session="test-session")
    client.command.assert_awaited_once_with(
        "evaluate",
        {"code": SCROLL_PAGE_JS},
        session="test-session",
    )


def _opening_count(data: dict) -> int:
    return sum(1 for post in data.get("posts", []) if post.get("isJobOpening"))


@pytest.mark.asyncio
async def test_scroll_until_count_stops_when_no_new_content():
    fixture = _load_posts_fixture()
    snapshots = [fixture, fixture]
    call_index = 0

    async def take_snapshot() -> dict:
        nonlocal call_index
        snap = snapshots[min(call_index, len(snapshots) - 1)]
        call_index += 1
        return snap

    client = AsyncMock()
    best, count, attempts = await scroll_until_count(
        client,
        session="test-session",
        target=5,
        max_scrolls=3,
        count_fn=_opening_count,
        take_snapshot=take_snapshot,
    )

    assert attempts == 1
    assert count == 2
    assert best is fixture
    assert client.command.await_count == 1


@pytest.mark.asyncio
async def test_scroll_until_count_stops_at_target():
    fixture = _load_posts_fixture()
    richer = dict(fixture)
    richer_posts = list(fixture.get("posts", [])) * 3
    richer["posts"] = richer_posts
    snapshots = [fixture, richer]
    call_index = 0

    async def take_snapshot() -> dict:
        nonlocal call_index
        snap = snapshots[min(call_index, len(snapshots) - 1)]
        call_index += 1
        return snap

    client = AsyncMock()
    best, count, attempts = await scroll_until_count(
        client,
        session="test-session",
        target=5,
        max_scrolls=5,
        count_fn=_opening_count,
        take_snapshot=take_snapshot,
    )

    assert attempts == 1
    assert count >= 5
    assert best is richer
