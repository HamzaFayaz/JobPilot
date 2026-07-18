"""Tests for search route wiring and worker status API."""

from unittest.mock import patch

from tests.conftest import login, signup


def _pair_and_heartbeat(client) -> str:
    response = client.post("/api/worker/pair")
    assert response.status_code == 200
    token = response.json()["workerToken"]
    heartbeat = client.post(
        "/api/worker/heartbeat",
        headers={"Authorization": f"Bearer {token}"},
        json={"browserHealth": "ready"},
    )
    assert heartbeat.status_code == 204
    return token


def _seed_profile_for_search(client) -> None:
    client.put(
        "/api/profile",
        json={
            "targetRoles": ["Python Developer"],
            "searchRole": "Python Developer",
            "searchPlatform": "linkedin",
            "searchCountry": "Pakistan",
            "searchWorkMode": "both",
            "searchMaxListings": 8,
            "searchJobAge": "week",
        },
    )


def test_worker_status_not_connected(test_db, client):
    signup(client, "status@example.com")
    login(client, "status@example.com")

    response = client.get("/api/worker/status")
    assert response.status_code == 200
    assert response.json()["connected"] is False


def test_worker_status_connected(test_db, client):
    signup(client, "connected@example.com")
    login(client, "connected@example.com")
    _pair_and_heartbeat(client)

    response = client.get("/api/worker/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["browserHealth"] == "ready"


def test_start_search_requires_helper(test_db, client):
    signup(client, "nohlp@example.com")
    login(client, "nohlp@example.com")
    _seed_profile_for_search(client)

    response = client.post("/api/search")
    assert response.status_code == 400
    assert "Search Helper is not connected" in response.json()["detail"]


@patch("backend.app.routes.search.run_parent_graph")
def test_start_search_enqueues_graph(mock_run_graph, test_db, client):
    user = signup(client, "search@example.com")
    login(client, "search@example.com")
    _seed_profile_for_search(client)
    _pair_and_heartbeat(client)

    response = client.post("/api/search")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["runId"] > 0
    mock_run_graph.assert_called_once_with(body["runId"], user["id"])


@patch("backend.app.routes.search.run_parent_graph")
def test_start_search_blocks_when_run_active(mock_run_graph, test_db, client):
    signup(client, "busy@example.com")
    login(client, "busy@example.com")
    _seed_profile_for_search(client)
    _pair_and_heartbeat(client)

    first = client.post("/api/search")
    assert first.status_code == 200
    second = client.post("/api/search")
    assert second.status_code == 409
    assert "already in progress" in second.json()["detail"]
    assert mock_run_graph.call_count == 1


def test_get_latest_run_returns_most_recent(test_db, client):
    signup(client, "latest@example.com")
    login(client, "latest@example.com")

    empty = client.get("/api/runs/latest")
    assert empty.status_code == 200
    assert empty.json() is None

    _seed_profile_for_search(client)
    _pair_and_heartbeat(client)

    first = client.post("/api/search")
    assert first.status_code == 200
    first_id = first.json()["runId"]

    latest = client.get("/api/runs/latest")
    assert latest.status_code == 200
    body = latest.json()
    assert body["runId"] == first_id
    assert body["status"] == "pending"
