"""HTTP client for JobPilot worker APIs."""

from typing import Any

import httpx

from worker.config import WorkerSettings
from worker.models import RawJobListing, WorkerTask


class JobPilotWorkerClient:
    def __init__(self, settings: WorkerSettings) -> None:
        self._settings = settings
        self._base = settings.jobpilot_api_base.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.worker_token}"}

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self._base, headers=self._headers, timeout=30.0)

    def send_heartbeat(self, *, browser_health: str = "ready") -> None:
        with self._client() as client:
            response = client.post(
                "/api/worker/heartbeat",
                json={"browserHealth": browser_health},
            )
            response.raise_for_status()

    def fetch_next_task(self) -> WorkerTask | None:
        with self._client() as client:
            response = client.get("/api/worker/tasks/next")
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return None
            data = response.json()
            if not data:
                return None
            return WorkerTask.model_validate(data)

    def post_result(
        self,
        task_id: str,
        listings: list[RawJobListing],
        *,
        warnings: list[str] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "listings": [item.model_dump(by_alias=True) for item in listings],
            "warnings": warnings or [],
        }
        with self._client() as client:
            response = client.post(f"/api/worker/tasks/{task_id}/result", json=payload)
            response.raise_for_status()

    def post_fail(self, task_id: str, *, error: str, code: str) -> None:
        with self._client() as client:
            response = client.post(
                f"/api/worker/tasks/{task_id}/fail",
                json={"error": error, "code": code},
            )
            response.raise_for_status()
