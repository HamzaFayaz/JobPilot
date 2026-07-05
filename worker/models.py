"""Local task models matching the JobPilot worker API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Platform = Literal["linkedin", "indeed"]
WorkMode = Literal["remote", "onsite", "both"]
JobAge = Literal["24h", "week", "month"]


class WorkerTask(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    task_id: str = Field(alias="taskId")
    run_id: int = Field(alias="runId")
    role: str
    platform: Platform
    country: str
    work_mode: WorkMode = Field(alias="workMode")
    max_listings: int = Field(alias="maxListings")
    job_age: JobAge = Field(alias="jobAge")
    max_job_age_days: int = Field(alias="maxJobAgeDays")
    skills_summary: str = Field(alias="skillsSummary")


class RawJobListing(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    title: str
    company: str
    url: str
    description_text: str = Field(default="", alias="descriptionText")
    source_platform: Platform = Field(alias="sourcePlatform")
