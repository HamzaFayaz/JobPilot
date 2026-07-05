"""Search task prompts for the WebBridge + Qwen ReAct agent loop."""

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
    age_label = _JOB_AGE_LABELS[task.job_age]
    jobs_target = max(task.max_listings // 2, 1)
    posts_target = max(task.max_listings - jobs_target, 0)

    return f"""Use ONE browser tab for the whole task.

PART A — LinkedIn Jobs section (official listings)
1. Navigate to https://www.linkedin.com/ (home page). Confirm you are logged in.
2. From the top navigation bar, click Jobs to open the Jobs area (prefer this over jumping straight to a deep URL).
3. In the Jobs search bar, enter role "{task.role}" and location "{task.country}", then run the search.
4. Open "All filters" (or the filter panel).
5. Under "Date posted", select "{date_filter}".
6. {workplace}
7. Apply filters and wait for results.
8. Open matching job cards. Collect up to {jobs_target} jobs posted within {age_label}.
   For each: title, company, job listing URL, description text.

PART B — LinkedIn Posts (hiring posts not in Jobs)
Many hiring managers post only in the feed, not in Jobs.
9. Go back to LinkedIn home or use the main top search bar.
10. Search Posts (switch result type to Posts).
11. Build the Posts query from THIS run only — role "{task.role}" and country "{task.country}".
    - Include a hiring intent word (e.g. hiring, we're hiring, looking for).
    - Use the user's actual role; you may add 1–2 close OR variants derived from "{task.role}".
    - Do NOT reuse example queries from instructions (e.g. do not hard-code "AI Engineer" unless that is the role).
    - Example shape only: hiring ("<role>" OR "<variant>") <country>
12. Prefer posts from {age_label}. Use LinkedIn's post date filter if available.
13. Open relevant posts. Extract title, company (or poster), post URL, and description from the post body.
    Collect up to {posts_target} additional listings (or whatever remains to reach {task.max_listings} total).

FINISH
- Merge Part A + Part B. Deduplicate by URL.
- Stop at {task.max_listings} total jobs OR when both sections are exhausted within {age_label}."""


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
