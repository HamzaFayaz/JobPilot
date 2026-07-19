"""Pydantic schemas for Search Helper worker APIs."""

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.browser import BrowserHealth, Platform, RawJobListing
from backend.app.models.search_prefs import JobAgePreset, WorkMode


class WorkerPairResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    worker_token: str = Field(alias="workerToken")


class WorkerStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    connected: bool
    browser_health: BrowserHealth | None = Field(default=None, alias="browserHealth")
    last_seen_at: str | None = Field(default=None, alias="lastSeenAt")
    label: str | None = None


class WorkerHeartbeatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    browser_health: BrowserHealth = Field(alias="browserHealth")


class WorkerTaskResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    task_id: str = Field(alias="taskId")
    run_id: int = Field(alias="runId")
    role: str
    platform: Platform
    country: str
    work_mode: WorkMode = Field(alias="workMode")
    max_listings: int = Field(alias="maxListings")
    job_age: JobAgePreset = Field(alias="jobAge")
    max_job_age_days: int = Field(alias="maxJobAgeDays")
    skills_summary: str = Field(alias="skillsSummary")
    agent_mode: str = Field(default="cloud", alias="agentMode")


class WorkerTaskResultRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    listings: list[RawJobListing]
    warnings: list[str] = Field(default_factory=list)


class WorkerTaskFailRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    error: str
    code: str


class WorkerAgentAttachResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    ok: bool = True
    agent_mode: str = Field(alias="agentMode")


class WorkerAgentCommandResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    type: str
    call_id: str | None = Field(default=None, alias="callId")
    name: str | None = None
    arguments: dict | None = None
    session: str | None = None
    error: str | None = None
    code: str | None = None


class WorkerAgentToolResultRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    call_id: str = Field(alias="callId")
    result: dict | list | str | int | float | bool | None = None
