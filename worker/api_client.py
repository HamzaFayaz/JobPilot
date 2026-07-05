"""HTTP client for JobPilot worker APIs."""

import logging
import time
from typing import Any

import httpx

from worker.config import WorkerSettings
from worker.models import RawJobListing, WorkerTask

logger = logging.getLogger(__name__)

_RETRYABLE = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.NetworkError,
)

# Exported for main.py loop logging.
RETRYABLE_API_ERRORS = _RETRYABLE


class JobPilotWorkerClient:
    def __init__(self, settings: WorkerSettings) -> None:
        self._settings = settings
        self._base = settings.jobpilot_api_base.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.worker_token}"}

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self._base, headers=self._headers, timeout=30.0)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Retry transient ECS/network drops (common when the API is busy)."""
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                with self._client() as client:
                    response = client.request(method, path, **kwargs)
                    response.raise_for_status()
                    return response
            except _RETRYABLE as exc:
                last_exc = exc
                wait = 1.5 * (attempt + 1)
                logger.warning(
                    "JobPilot API %s %s failed (%s) — retry in %.1fs",
                    method,
                    path,
                    exc,
                    wait,
                )
                time.sleep(wait)
        assert last_exc is not None
        raise last_exc

    def send_heartbeat(self, *, browser_health: str = "ready") -> None:
        self._request(
            "POST",
            "/api/worker/heartbeat",
            json={"browserHealth": browser_health},
        )

    def fetch_next_task(self) -> WorkerTask | None:
        response = self._request("GET", "/api/worker/tasks/next")
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
        self._request("POST", f"/api/worker/tasks/{task_id}/result", json=payload)

    def post_fail(self, task_id: str, *, error: str, code: str) -> None:
        self._request(
            "POST",
            f"/api/worker/tasks/{task_id}/fail",
            json={"error": error, "code": code},
        )
