"""Browser-Use task prompts for search jobs."""

from worker.models import JobAge, Platform, WorkerTask

_JOB_AGE_LABELS: dict[JobAge, str] = {
    "24h": "the last 24 hours",
    "week": "the last 7 days",
    "month": "the last 30 days",
}

_WORK_MODE_INSTRUCTIONS = {
    "remote": "Include only remote or work-from-home jobs.",
    "onsite": "Include only on-site or in-office jobs.",
    "both": "Include remote, hybrid, and on-site jobs.",
}


def build_search_task(task: WorkerTask) -> str:
    platform_name = "LinkedIn" if task.platform == "linkedin" else "Indeed"
    age_label = _JOB_AGE_LABELS[task.job_age]
    work_mode = _WORK_MODE_INSTRUCTIONS[task.work_mode]
    skills = task.skills_summary.strip()

    skills_line = f"Candidate skills (hint only): {skills}.\n" if skills else ""

    return f"""Search {platform_name} for "{task.role}" jobs in {task.country}.
{work_mode}
Only collect jobs posted within {age_label}.
{skills_line}Stop and finish when EITHER:
  • you collected {task.max_listings} matching jobs, OR
  • there are no more matching jobs within {age_label}.

For each job return one JSON object with:
  title, company, url, descriptionText, sourcePlatform="{task.platform}"

When finished, return ONLY a JSON array of job objects. No markdown fences or extra text.
Example:
[
  {{
    "title": "Python Developer",
    "company": "Acme",
    "url": "https://www.linkedin.com/jobs/view/123",
    "descriptionText": "Build APIs with FastAPI",
    "sourcePlatform": "{task.platform}"
  }}
]"""
