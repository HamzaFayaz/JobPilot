"""Search Helper worker API routes."""

import json

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.deps.auth import get_current_user
from backend.app.deps.worker import get_worker_device
from backend.app.models.worker import (
    WorkerHeartbeatRequest,
    WorkerPairResponse,
    WorkerStatusResponse,
    WorkerTaskFailRequest,
    WorkerTaskResponse,
    WorkerTaskResultRequest,
)
from backend.app.services.worker_store import (
    claim_next_worker_task,
    complete_worker_task,
    create_worker_device,
    fail_worker_task,
    get_active_worker_device,
    get_worker_task,
    revoke_worker_devices,
    update_worker_heartbeat,
)

router = APIRouter(prefix="/api/worker", tags=["worker"])


@router.post("/pair", response_model=WorkerPairResponse)
def pair_worker(current_user: dict = Depends(get_current_user)) -> WorkerPairResponse:
    revoke_worker_devices(current_user["id"])
    token = create_worker_device(current_user["id"])
    return WorkerPairResponse(workerToken=token)


@router.delete("/pair", status_code=status.HTTP_204_NO_CONTENT)
def unpair_worker(current_user: dict = Depends(get_current_user)) -> None:
    revoke_worker_devices(current_user["id"])


@router.get("/status", response_model=WorkerStatusResponse)
def get_worker_status(current_user: dict = Depends(get_current_user)) -> WorkerStatusResponse:
    device = get_active_worker_device(current_user["id"])
    if not device:
        return WorkerStatusResponse(connected=False)

    return WorkerStatusResponse(
        connected=True,
        browser_health=device.get("browser_health"),
        last_seen_at=device.get("last_seen_at"),
        label=device.get("label"),
    )


@router.post("/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
def worker_heartbeat(
    body: WorkerHeartbeatRequest,
    device: dict = Depends(get_worker_device),
) -> None:
    update_worker_heartbeat(device["id"], browser_health=body.browser_health)


@router.get("/tasks/next", response_model=WorkerTaskResponse | None)
def get_next_worker_task(
    device: dict = Depends(get_worker_device),
) -> WorkerTaskResponse | None:
    task = claim_next_worker_task(device["user_id"])
    if not task:
        return None

    payload = json.loads(task["payload_json"])
    return WorkerTaskResponse.model_validate(payload)


@router.post("/tasks/{task_id}/result", status_code=status.HTTP_204_NO_CONTENT)
def post_worker_task_result(
    task_id: str,
    body: WorkerTaskResultRequest,
    device: dict = Depends(get_worker_device),
) -> None:
    task = get_worker_task(task_id)
    if not task or task["user_id"] != device["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    listings = [listing.model_dump(by_alias=True) for listing in body.listings]
    if not complete_worker_task(
        task_id,
        user_id=device["user_id"],
        listings=listings,
        warnings=body.warnings,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not open for a result",
        )


@router.post("/tasks/{task_id}/fail", status_code=status.HTTP_204_NO_CONTENT)
def post_worker_task_fail(
    task_id: str,
    body: WorkerTaskFailRequest,
    device: dict = Depends(get_worker_device),
) -> None:
    task = get_worker_task(task_id)
    if not task or task["user_id"] != device["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if not fail_worker_task(
        task_id,
        user_id=device["user_id"],
        error=body.error,
        code=body.code,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not open for failure",
        )
