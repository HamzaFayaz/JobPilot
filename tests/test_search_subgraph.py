"""Tests for ECS search subgraph enqueue + wait flow."""

import threading

from backend.app.db import get_connection
from backend.app.graph.subgraphs.search.graph import (
    enqueue_browser_task,
    wait_for_listings,
)
from backend.app.graph.subgraphs.search.state import SearchState
from backend.app.services.search_store import get_search_run
from backend.app.services.worker_store import get_worker_task

from tests.conftest import login, signup


def _search_state(
    *,
    run_id: int,
    user_id: int,
    role: str = "Python Developer",
    task_id: str = "",
    skills_summary: str = "Python, FastAPI, SQLite",
    country: str = "Pakistan",
    work_mode: str = "both",
    max_listings: int = 8,
    job_age: str = "week",
) -> SearchState:
    return SearchState(
        run_id=run_id,
        user_id=user_id,
        role=role,
        platform="linkedin",
        country=country,
        work_mode=work_mode,
        max_listings=max_listings,
        job_age=job_age,
        skills_summary=skills_summary,
        task_id=task_id,
        raw_listings=[],
        listings=[],
        warnings=[],
        errors=[],
    )


def _seed_run(user_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO search_runs (
                user_id, role, platform, country, work_mode, max_listings, job_age, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, "Python Developer", "linkedin", "Pakistan", "both", 8, "week", "running"),
        )
        conn.commit()
        return int(cursor.lastrowid)


def _pair_worker(client) -> str:
    response = client.post("/api/worker/pair")
    assert response.status_code == 200, response.text
    return response.json()["workerToken"]


def _heartbeat_worker(client, worker_token: str) -> None:
    response = client.post(
        "/api/worker/heartbeat",
        headers={"Authorization": f"Bearer {worker_token}"},
        json={"browserHealth": "ready"},
    )
    assert response.status_code == 204, response.text


def test_enqueue_browser_task_creates_worker_task(test_db, client):
    user = signup(client, "enqueue@example.com")
    login(client, "enqueue@example.com")
    worker_token = _pair_worker(client)
    _heartbeat_worker(client, worker_token)

    run_id = _seed_run(user["id"])
    result = enqueue_browser_task(_search_state(run_id=run_id, user_id=user["id"]))

    assert result["task_id"]
    assert result["errors"] == []

    task = get_worker_task(result["task_id"])
    assert task is not None
    assert task["status"] == "pending"
    assert task["run_id"] == run_id
    assert task["user_id"] == user["id"]


def test_enqueue_fails_when_helper_offline(test_db, client):
    user = signup(client, "offline@example.com")
    run_id = _seed_run(user["id"])

    result = enqueue_browser_task(_search_state(run_id=run_id, user_id=user["id"]))

    assert result["errors"]
    assert "Search Helper not connected" in result["errors"][0]

    run = get_search_run(run_id)
    assert run is not None
    assert run["status"] == "failed"


def test_wait_for_listings_receives_worker_result(test_db, client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.graph.subgraphs.search.graph.wait_for_worker_task_result",
        lambda task_id: {
            "status": "completed",
            "result": {
                "listings": [
                    {
                        "title": "Python Developer",
                        "company": "Acme",
                        "url": "https://www.linkedin.com/jobs/view/123",
                        "descriptionText": "Build APIs",
                        "sourcePlatform": "linkedin",
                    }
                ],
                "warnings": ["captcha encountered"],
            },
            "warnings": ["captcha encountered"],
        },
    )

    user = signup(client, "wait@example.com")
    run_id = _seed_run(user["id"])
    state = _search_state(run_id=run_id, user_id=user["id"], task_id="task-123")

    result = wait_for_listings(state)

    assert result["errors"] == []
    assert len(result["raw_listings"]) == 1
    assert result["raw_listings"][0].title == "Python Developer"
    assert result["warnings"] == ["captcha encountered"]


def test_worker_result_endpoint_completes_task(test_db, client):
    user = signup(client, "worker-result@example.com")
    login(client, "worker-result@example.com")
    worker_token = _pair_worker(client)
    _heartbeat_worker(client, worker_token)

    run_id = _seed_run(user["id"])
    enqueue_result = enqueue_browser_task(
        _search_state(run_id=run_id, user_id=user["id"])
    )
    task_id = enqueue_result["task_id"]

    next_task = client.get(
        "/api/worker/tasks/next",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert next_task.status_code == 200
    assert next_task.json()["taskId"] == task_id
    assert next_task.json()["role"] == "Python Developer"
    assert next_task.json()["country"] == "Pakistan"
    assert next_task.json()["workMode"] == "both"
    assert next_task.json()["maxListings"] == 8
    assert next_task.json()["jobAge"] == "week"
    assert next_task.json()["maxJobAgeDays"] == 7
    assert next_task.json()["agentMode"] == "cloud"

    response = client.post(
        f"/api/worker/tasks/{task_id}/result",
        headers={"Authorization": f"Bearer {worker_token}"},
        json={
            "listings": [
                {
                    "title": "Backend Engineer",
                    "company": "Beta Corp",
                    "url": "https://www.linkedin.com/jobs/view/456",
                    "descriptionText": "FastAPI services",
                    "sourcePlatform": "linkedin",
                }
            ],
            "warnings": [],
        },
    )
    assert response.status_code == 204

    task = get_worker_task(task_id)
    assert task is not None
    assert task["status"] == "completed"
    assert "Backend Engineer" in task["result_json"]


def test_wait_for_listings_polls_until_worker_posts_result(test_db, client, monkeypatch):
    import time

    monkeypatch.setattr("backend.app.config.settings.browser_search_wait_timeout_seconds", 10)
    monkeypatch.setattr("backend.app.services.worker_store.time.sleep", lambda _: None)
    # Avoid real Dashscope rewrite blocking past the wait timeout.
    monkeypatch.setattr(
        "backend.app.routes.worker.rewrite_listings",
        lambda listings: listings,
    )

    user = signup(client, "poll@example.com")
    login(client, "poll@example.com")
    worker_token = _pair_worker(client)
    _heartbeat_worker(client, worker_token)

    run_id = _seed_run(user["id"])
    enqueue_result = enqueue_browser_task(
        _search_state(run_id=run_id, user_id=user["id"])
    )
    task_id = enqueue_result["task_id"]

    def _post_result_later() -> None:
        time.sleep(0.05)
        client.post(
            f"/api/worker/tasks/{task_id}/result",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "listings": [
                    {
                        "title": "Data Engineer",
                        "company": "Gamma",
                        "url": "https://www.linkedin.com/jobs/view/789",
                        "descriptionText": "ETL pipelines",
                        "sourcePlatform": "linkedin",
                    }
                ]
            },
        )

    thread = threading.Thread(target=_post_result_later)
    thread.start()

    result = wait_for_listings(
        _search_state(run_id=run_id, user_id=user["id"], task_id=task_id)
    )
    thread.join(timeout=5)

    assert result["errors"] == []
    assert len(result["raw_listings"]) == 1
    assert result["raw_listings"][0].company == "Gamma"
