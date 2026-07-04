"""Tests for init_run graph node."""

from backend.app.db import get_connection
from backend.app.graph.nodes.init_run import init_run
from backend.app.graph.state import RunState
from backend.app.services.profile_store import update_cv
from backend.app.services.search_store import get_search_run

from tests.conftest import signup


def _seed_run(user_id: int, *, role: str = "Python Developer", status: str = "pending") -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO search_runs (user_id, role, platform, status)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, role, "linkedin", status),
        )
        conn.commit()
        return int(cursor.lastrowid)


def _seed_profile(user_id: int) -> None:
    update_cv(
        user_id,
        filename="cv.docx",
        path="/tmp/cv.docx",
        cv_text="Experienced Python developer with FastAPI experience.",
        skills=["Python", "FastAPI", "SQLite"],
        status="ready",
    )
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE profiles
            SET projects = ?, target_roles = ?
            WHERE user_id = ?
            """,
            (
                '[{"id":"p1","name":"JobPilot","description":"Job search copilot","source":"manual"}]',
                '["Python Developer"]',
                user_id,
            ),
        )
        conn.commit()


def _run_state(run_id: int, user_id: int) -> RunState:
    return RunState(
        run_id=run_id,
        user_id=user_id,
        role="",
        platform="linkedin",
        profile={"cv_text": "", "skills": [], "target_roles": [], "projects": []},
        listings=[],
        matched_jobs=[],
        packages=[],
        errors=[],
        status="pending",
    )


def test_init_run_hydrates_profile_and_sets_running(test_db, client):
    user = signup(client, "init-run@example.com")
    user_id = user["id"]
    _seed_profile(user_id)
    run_id = _seed_run(user_id)

    result = init_run(_run_state(run_id, user_id))

    assert result["status"] == "running"
    assert result["role"] == "Python Developer"
    assert result["platform"] == "linkedin"
    assert result["profile"]["cv_text"]
    assert len(result["profile"]["skills"]) == 3
    assert len(result["profile"]["projects"]) == 1

    run = get_search_run(run_id)
    assert run is not None
    assert run["status"] == "running"


def test_init_run_fails_without_cv(test_db, client):
    user = signup(client, "no-cv@example.com")
    user_id = user["id"]
    run_id = _seed_run(user_id)

    result = init_run(_run_state(run_id, user_id))

    assert result["status"] == "failed"
    assert "CV is required" in result["errors"][0]

    run = get_search_run(run_id)
    assert run is not None
    assert run["status"] == "failed"
    assert run["error"]


def test_init_run_rejects_wrong_user(test_db, client):
    owner = signup(client, "owner@example.com")
    other = signup(client, "other@example.com")
    _seed_profile(owner["id"])
    run_id = _seed_run(owner["id"])

    result = init_run(_run_state(run_id, other["id"]))

    assert result["status"] == "failed"
    assert "does not belong" in result["errors"][0]
