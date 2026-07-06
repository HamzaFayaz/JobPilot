"""Build LinkedIn search URLs from worker task fields (navigate-first, no UI filters)."""

from __future__ import annotations

from urllib.parse import urlencode

from worker.models import JobAge, WorkerTask, WorkMode

_JOBS_BASE = "https://www.linkedin.com/jobs/search/"
_POSTS_BASE = "https://www.linkedin.com/search/results/content/"

# Seconds in f_TPR=r{seconds} — mirrors LinkedIn job search date presets.
_JOB_TPR: dict[JobAge, str] = {
    "24h": "r86400",
    "week": "r604800",
    "month": "r2592000",
}

_POSTS_DATE: dict[JobAge, str] = {
    "24h": "past-24h",
    "week": "past-week",
    "month": "past-month",
}

# f_WT workplace codes: on-site=1, remote=2, hybrid=3; all three = "2,1,3".
_JOB_WORKPLACE: dict[WorkMode, str] = {
    "remote": "2",
    "onsite": "1",
    "both": "2,1,3",
}


def _posts_keywords(task: WorkerTask) -> str:
    """Hiring-intent query for content search; remote adds a keyword hint."""
    role = task.role.strip()
    country = task.country.strip()
    if task.work_mode == "remote":
        return f'hiring "{role}" remote {country}'
    return f'hiring "{role}" {country}'


def linkedin_jobs_search_url(task: WorkerTask) -> str:
    """Jobs section: role + location + date posted + most relevant + workplace."""
    params: list[tuple[str, str]] = [
        ("keywords", task.role.strip()),
        ("location", task.country.strip()),
        ("f_TPR", _JOB_TPR[task.job_age]),
        ("sortBy", "R"),
        ("f_WT", _JOB_WORKPLACE[task.work_mode]),
        ("origin", "JOB_SEARCH_PAGE_JOB_FILTER"),
    ]
    return _JOBS_BASE + "?" + urlencode(params)


def linkedin_posts_search_url(task: WorkerTask) -> str:
    """Posts section: hiring query + date posted + top match (relevance)."""
    date_value = _POSTS_DATE[task.job_age]
    params: list[tuple[str, str]] = [
        ("keywords", _posts_keywords(task)),
        ("datePosted", f'["{date_value}"]'),
        ("sortBy", '["relevance"]'),
        ("origin", "FACETED_SEARCH"),
    ]
    return _POSTS_BASE + "?" + urlencode(params)
