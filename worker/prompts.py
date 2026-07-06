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

# Minimum LLM steps per LinkedIn phase (workflow nav/search/filters), independent of
# max_listings from the ECS task. Listing target still comes from the system task.
LINKEDIN_JOBS_STEP_FLOOR = 12
LINKEDIN_POSTS_STEP_FLOOR = 8

_INDEED_DATE_FILTER = {
    "24h": "Last 24 hours",
    "week": "Last 7 days",
    "month": "Last 30 days",
}


def listing_targets(max_listings: int) -> tuple[int, int]:
    """Split max_listings between LinkedIn Jobs and Posts sections."""
    jobs = max(max_listings // 2, 1)
    posts = max(max_listings - jobs, 0)
    return jobs, posts


def max_steps_for_target(target: int, *, ceiling: int = 15) -> int:
    """Step budget scales with how many listings this phase should collect."""
    if target <= 0:
        return 0
    return min(ceiling, max(6, target * 3))


def linkedin_phase_steps(target: int, *, floor: int, ceiling: int = 15) -> int:
    """LinkedIn phase budget: workflow floor plus listing-scaled cap."""
    if target <= 0:
        return 0
    return max(floor, max_steps_for_target(target, ceiling=ceiling))


def linkedin_jobs_steps(target: int, *, ceiling: int = 15) -> int:
    return linkedin_phase_steps(target, floor=LINKEDIN_JOBS_STEP_FLOOR, ceiling=ceiling)


def linkedin_posts_steps(target: int, *, ceiling: int = 15) -> int:
    return linkedin_phase_steps(target, floor=LINKEDIN_POSTS_STEP_FLOOR, ceiling=ceiling)


def _trim_skills(skills: str, *, max_chars: int = 240) -> str:
    skills = skills.strip()
    if len(skills) <= max_chars:
        return skills
    trimmed = skills[:max_chars].rsplit(",", 1)[0].strip()
    return f"{trimmed}, ..." if trimmed else skills[:max_chars]


def _json_output_footer(task: WorkerTask, *, target: int, phase: str = "jobs") -> str:
    if phase == "posts":
        return f"""Stop when you have {target} matching job openings OR there are no more results in scope.

For each opening return one JSON object with:
  title, company, url, descriptionText, sourcePlatform="{task.platform}"

descriptionText is required — copy the entire post body from snapshot `posts[]` (apply email, phone, WhatsApp, requirements — everything visible).
url is optional when apply/contact details are in descriptionText.

When finished, return ONLY a JSON array of job objects. No markdown fences or extra text.
You may return `[]` — the worker will fill listings from `posts[]` when needed."""

    return f"""Stop when you have {target} matching jobs OR there are no more results in scope.

For each job return one JSON object with:
  title, company, url, descriptionText, sourcePlatform="{task.platform}"

descriptionText is required — copy it from the snapshot "About the job" section after opening a job card.
For url, use window.location.href via evaluate after opening the job (must be a /jobs/view/ link).
title and company must match the list row you clicked.

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


def _linkedin_jobs_steps(task: WorkerTask, *, target: int) -> str:
    age_label = _JOB_AGE_LABELS[task.job_age]
    workplace = _WORK_MODE_LINKEDIN_FILTERS[task.work_mode]

    return f"""Use ONE browser tab dedicated to this phase only (isolated from the other LinkedIn phase).

LinkedIn Jobs section (official job listings)
You start on a pre-filtered Jobs search results page for "{task.role}" in {task.country}
({age_label}, most relevant sort, {workplace.lower()}).

Workflow for each job (repeat until you have {target} or none remain):
1. Snapshot the left results list — refs change after every click.
2. Click ONE job card from the fresh snapshot.
3. Snapshot again and read title, company, and description from the right-rail detail panel
   (look for the "About the job" heading and text below it).
4. Use evaluate ONLY to read window.location.href — that is the job url (must contain /jobs/view/).
5. Go back to the results list before the next job.
6. If you need more rows, scroll the list with evaluate: `window.scrollBy(0, window.innerHeight)` then snapshot again.

Rules:
- Do NOT use evaluate with CSS selectors for description — read it from the snapshot.
- title and company in JSON must match the list row you clicked.
- Collect up to {target} jobs posted within {age_label}.

Do NOT search Posts in this phase — Jobs section only."""


def _linkedin_posts_steps(task: WorkerTask, *, target: int) -> str:
    age_label = _JOB_AGE_LABELS[task.job_age]
    remote_hint = (
        ' Include "remote" in scope.'
        if task.work_mode == "remote"
        else ""
    )

    return f"""Use ONE browser tab dedicated to this phase only (isolated from the other LinkedIn phase).

LinkedIn Posts (hiring posts on the search results page)
You start on a pre-filtered Posts search page for hiring posts about
"{task.role}" in {task.country} ({age_label}, top match sort).{remote_hint}
The browser is already on that page — do NOT call navigate to the search URL again.

Workflow:
1. Snapshot the results page — each snapshot includes a structured `posts[]` array with
   title, company, location, descriptionText, and url (when available). Read from `posts[]`.
2. Do NOT click post rows, author names, or timestamps — that opens profiles, not posts.
3. Build JSON from hiring posts where `isJobOpening` is true (skip debate/rant posts).
4. If you have fewer than {target} openings, use evaluate to scroll:
   `window.scrollBy(0, window.innerHeight)` then snapshot again and merge new posts.
5. Stop when you have {target} openings or no new posts appear after scrolling.

Rules:
- Extract all fields from `posts[]` in the snapshot — do not open individual posts.
- `descriptionText` must be the complete post body (not a summary).
- `url` from `posts[]` is optional when apply info is in descriptionText. Never use profile /in/ URLs.
- Collect up to {target} job openings.

Do NOT return to the Jobs section in this phase — Posts only."""


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


def build_linkedin_jobs_task(task: WorkerTask, *, target: int) -> str:
    skills = _trim_skills(task.skills_summary)
    skills_line = f"Candidate skills (hint only): {skills}.\n" if skills else ""
    return f"""Search LinkedIn Jobs for "{task.role}" jobs in {task.country}.

{_linkedin_jobs_steps(task, target=target)}

{skills_line}{_json_output_footer(task, target=target, phase="jobs")}"""


def build_linkedin_posts_task(task: WorkerTask, *, target: int) -> str:
    skills = _trim_skills(task.skills_summary)
    skills_line = f"Candidate skills (hint only): {skills}.\n" if skills else ""
    return f"""Search LinkedIn Posts for "{task.role}" hiring posts in {task.country}.

{_linkedin_posts_steps(task, target=target)}

{skills_line}{_json_output_footer(task, target=target, phase="posts")}"""


def build_indeed_task(task: WorkerTask) -> str:
    age_label = _JOB_AGE_LABELS[task.job_age]
    skills = _trim_skills(task.skills_summary)
    skills_line = f"Candidate skills (hint only): {skills}.\n" if skills else ""
    return f"""Search Indeed for "{task.role}" jobs in {task.country}.

{_indeed_steps(task)}

{skills_line}Stop when you have {task.max_listings} matching jobs OR there are no more within {age_label}.

{_json_output_footer(task, target=task.max_listings)}"""


def build_search_task(task: WorkerTask) -> str:
    """Single-phase task prompt (Indeed, or legacy single-loop LinkedIn)."""
    if task.platform == "linkedin":
        jobs_target, _ = listing_targets(task.max_listings)
        return build_linkedin_jobs_task(task, target=jobs_target)
    return build_indeed_task(task)
