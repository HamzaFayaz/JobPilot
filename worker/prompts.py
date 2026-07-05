"""Search task prompts for the browser agent (WebBridge ReAct loop).

Browser-Use one-shot task strings are deprecated — prompts feed Qwen tool-calling loop.
See System Design/kimi-webbridge-provider.md
"""

from worker.models import JobAge, Platform, WorkerTask

_JOB_AGE_LABELS: dict[JobAge, str] = {
    "24h": "the last 24 hours",
    "week": "the last 7 days",
    "month": "the last 30 days",
}

_WORK_MODE_LINKEDIN_FILTERS = {
    "remote": 'In All filters, set Workplace type to "Remote" only.',
    "onsite": 'In All filters, set Workplace type to "On-site" only.',
    "both": "Include remote, hybrid, and on-site jobs (no workplace-type restriction).",
}

_LINKEDIN_DATE_FILTER = {
    "24h": "Past 24 hours",
    "week": "Past week",
    "month": "Past month",
}

_INDEED_DATE_FILTER = {
    "24h": "Last 24 hours",
    "week": "Last 7 days",
    "month": "Last 30 days",
}


def _trim_skills(skills: str, *, max_chars: int = 240) -> str:
    skills = skills.strip()
    if len(skills) <= max_chars:
        return skills
    trimmed = skills[:max_chars].rsplit(",", 1)[0].strip()
    return f"{trimmed}, ..." if trimmed else skills[:max_chars]


def _linkedin_steps(task: WorkerTask) -> str:
    date_filter = _LINKEDIN_DATE_FILTER[task.job_age]
    workplace = _WORK_MODE_LINKEDIN_FILTERS[task.work_mode]
    return f"""Steps (one browser tab only — do not open new tabs):
1. Go to https://www.linkedin.com/jobs/
2. In the LinkedIn Jobs search bar, enter role "{task.role}" and location "{task.country}", then run the search.
3. Open "All filters" (or the filter panel).
4. Under "Date posted", select "{date_filter}".
5. {workplace}
6. Apply filters and wait for results to load.
7. Open matching job cards one by one. Collect up to {task.max_listings} jobs posted within {_JOB_AGE_LABELS[task.job_age]}."""


def _indeed_steps(task: WorkerTask) -> str:
    date_filter = _INDEED_DATE_FILTER[task.job_age]
    work_mode = {
        "remote": "Set remote / work from home filter if available.",
        "onsite": "Prefer on-site jobs only if a filter exists.",
        "both": "Include remote and on-site jobs.",
    }[task.work_mode]
    return f"""Steps (one browser tab only):
1. Go to https://www.indeed.com/
2. Search for "{task.role}" in "{task.country}".
3. Set date posted to "{date_filter}" if available. {work_mode}
4. Collect up to {task.max_listings} matching jobs."""


def build_search_task(task: WorkerTask) -> str:
    platform_name = "LinkedIn" if task.platform == "linkedin" else "Indeed"
    age_label = _JOB_AGE_LABELS[task.job_age]
    skills = _trim_skills(task.skills_summary)
    skills_line = f"Candidate skills (hint only): {skills}.\n" if skills else ""

    steps = _linkedin_steps(task) if task.platform == "linkedin" else _indeed_steps(task)

    return f"""Search {platform_name} for "{task.role}" jobs in {task.country}.

{steps}

{skills_line}Stop when you have {task.max_listings} matching jobs OR there are no more within {age_label}.

For each job return one JSON object with:
  title, company, url, descriptionText, sourcePlatform="{task.platform}"

When finished, return ONLY a JSON array of job objects. No markdown fences or extra text.
Example shape (use each job's real listing URL):
[
  {{
    "title": "Python Developer",
    "company": "Acme",
    "url": "https://example.com/job-listing",
    "descriptionText": "Build APIs with FastAPI",
    "sourcePlatform": "{task.platform}"
  }}
]"""
