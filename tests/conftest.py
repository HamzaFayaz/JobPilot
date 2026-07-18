"""Shared pytest fixtures for JobPilot backend tests."""

import os

import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("DATA_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-jobpilot")


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Isolated SQLite database per test."""
    db_path = tmp_path / "test_jobpilot.db"
    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.config.settings.db_path", db_path)
    monkeypatch.setattr("backend.app.config.settings.uploads_dir", uploads)
    monkeypatch.setattr("backend.app.config.settings.data_dir", tmp_path)
    monkeypatch.setattr("backend.app.config.settings.faiss_dir", tmp_path / "faiss")

    from backend.app.db import init_db
    from backend.app.services import crypto

    crypto._fernet = None
    init_db()
    yield db_path


@pytest.fixture
def client(test_db):
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with TestClient(app) as test_client:
        yield test_client


def signup(client, email: str, password: str = "password123") -> dict:
    response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client, email: str, password: str = "password123") -> dict:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()
