"""Shared search preference types and helpers."""

from typing import Literal

WorkMode = Literal["remote", "onsite", "both"]
JobAgePreset = Literal["24h", "week", "month"]

DEFAULT_WORK_MODE: WorkMode = "both"
DEFAULT_JOB_AGE: JobAgePreset = "week"
DEFAULT_MAX_LISTINGS = 8
MIN_MAX_LISTINGS = 1
MAX_MAX_LISTINGS = 20

JOB_AGE_DAYS: dict[JobAgePreset, int] = {
    "24h": 1,
    "week": 7,
    "month": 30,
}


def job_age_to_days(preset: JobAgePreset) -> int:
    return JOB_AGE_DAYS[preset]


def clamp_max_listings(value: int) -> int:
    return max(MIN_MAX_LISTINGS, min(MAX_MAX_LISTINGS, value))
