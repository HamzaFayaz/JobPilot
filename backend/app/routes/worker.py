"""Search Helper worker API routes."""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.deps.auth import get_current_user
from backend.app.deps.worker import get_worker_device
from backend.app.models.worker import (
    WorkerAgentAttachResponse,
    WorkerAgentCommandResponse,
    WorkerAgentToolResultRequest,
    WorkerHeartbeatRequest,
    WorkerPairResponse,
    WorkerStatusResponse,
    WorkerTaskFailRequest,
    WorkerTaskResponse,
    WorkerTaskResultRequest,
)
from backend.app.services.browser_agent.runner import run_cloud_browser_agent
from backend.app.services.browser_agent.session import get_or_create_session, get_session
from backend.app.services.listing_rewrite import rewrite_listings
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/worker", tags=["worker"])


def _require_claimed_task(task_id: str, device: dict) -> dict:
    task = get_worker_task(task_id)
    if not task or task["user_id"] != device["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task["status"] not in ("claimed", "pending"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is {task['status']}",
        )
    return task


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

    listings_models = rewrite_listings(list(body.listings))
    listings = [listing.model_dump(by_alias=True) for listing in listings_models]
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


@router.post(
    "/tasks/{task_id}/agent/attach",
    response_model=WorkerAgentAttachResponse,
)
async def attach_cloud_agent(
    task_id: str,
    device: dict = Depends(get_worker_device),
) -> WorkerAgentAttachResponse:
    """Worker is ready to execute tools; start the cloud ReAct loop if needed."""
    task = _require_claimed_task(task_id, device)
    payload = json.loads(task["payload_json"])
    agent_mode = str(payload.get("agentMode") or "cloud").lower()
    if agent_mode != "cloud":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is not in cloud agent mode",
        )

    session = get_or_create_session(task_id, device["user_id"])
    with session._start_lock:
        if not session.agent_started:
            session.agent_started = True
            session.status = "starting"
            asyncio.create_task(
                run_cloud_browser_agent(session=session, task_payload=payload),
                name=f"cloud-browser-agent-{task_id}",
            )
            logger.info("Started cloud browser agent for task %s", task_id)

    return WorkerAgentAttachResponse(ok=True, agentMode="cloud")


@router.get(
    "/tasks/{task_id}/agent/next",
    response_model=WorkerAgentCommandResponse | None,
)
async def poll_agent_command(
    task_id: str,
    timeout: float = Query(default=25.0, ge=1.0, le=55.0),
    device: dict = Depends(get_worker_device),
) -> WorkerAgentCommandResponse | None:
    """Long-poll for the next tool command from the cloud agent."""
    task = get_worker_task(task_id)
    if not task or task["user_id"] != device["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task["status"] in ("completed", "failed"):
        return WorkerAgentCommandResponse(
            type="done" if task["status"] == "completed" else "fail",
            error=task.get("error"),
            code=task.get("error_code"),
        )

    session = get_session(task_id)
    if not session:
        return None

    item = await asyncio.to_thread(
        session.wait_for_command_sync, timeout_seconds=timeout
    )
    if item is None:
        return None

    return WorkerAgentCommandResponse(
        type=item.type,
        callId=item.call_id,
        name=item.name,
        arguments=item.arguments,
        session=item.session,
        error=item.error,
        code=item.code,
    )


@router.post(
    "/tasks/{task_id}/agent/tool-result",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def post_agent_tool_result(
    task_id: str,
    body: WorkerAgentToolResultRequest,
    device: dict = Depends(get_worker_device),
) -> None:
    task = get_worker_task(task_id)
    if not task or task["user_id"] != device["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    session = get_session(task_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active cloud agent session",
        )

    if not session.submit_tool_result(body.call_id, body.result):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unknown or expired tool call id",
        )
