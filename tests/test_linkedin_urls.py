"""Tests for LinkedIn navigate-first search URL builders."""

from urllib.parse import parse_qs, urlparse

from worker.linkedin_urls import linkedin_jobs_search_url, linkedin_posts_search_url
from worker.models import WorkerTask

_FLUTTER_ROLE = "Flutter Developer"
_COUNTRY = "Pakistan"


def _task(*, work_mode: str) -> WorkerTask:
    return WorkerTask(
        taskId="t-flutter",
        runId=1,
        role=_FLUTTER_ROLE,
        platform="linkedin",
        country=_COUNTRY,
        workMode=work_mode,
        maxListings=4,
        jobAge="week",
        maxJobAgeDays=7,
        skillsSummary="Dart, Flutter",
    )


def test_jobs_flutter_developer_both_workplace_types():
    url = linkedin_jobs_search_url(_task(work_mode="both"))
    parsed = parse_qs(urlparse(url).query)

    assert url.startswith("https://www.linkedin.com/jobs/search/?")
    assert parsed["keywords"] == [_FLUTTER_ROLE]
    assert parsed["location"] == [_COUNTRY]
    assert parsed["f_TPR"] == ["r604800"]
    assert parsed["sortBy"] == ["R"]
    assert parsed["f_WT"] == ["2,1,3"]
    assert parsed["origin"] == ["JOB_SEARCH_PAGE_JOB_FILTER"]
    assert "sortBy=DD" not in url


def test_jobs_flutter_developer_remote_only():
    url = linkedin_jobs_search_url(_task(work_mode="remote"))
    parsed = parse_qs(urlparse(url).query)

    assert parsed["keywords"] == [_FLUTTER_ROLE]
    assert parsed["location"] == [_COUNTRY]
    assert parsed["f_TPR"] == ["r604800"]
    assert parsed["sortBy"] == ["R"]
    assert parsed["f_WT"] == ["2"]
    assert parsed["origin"] == ["JOB_SEARCH_PAGE_JOB_FILTER"]


def test_jobs_flutter_developer_onsite_only():
    url = linkedin_jobs_search_url(_task(work_mode="onsite"))
    parsed = parse_qs(urlparse(url).query)

    assert parsed["f_WT"] == ["1"]


def test_posts_flutter_developer_both_workplace_types():
    url = linkedin_posts_search_url(_task(work_mode="both"))
    parsed = parse_qs(urlparse(url).query)

    assert url.startswith("https://www.linkedin.com/search/results/content/?")
    assert parsed["keywords"] == [f'hiring "{_FLUTTER_ROLE}" {_COUNTRY}']
    assert parsed["datePosted"] == ['["past-week"]']
    assert parsed["sortBy"] == ['["relevance"]']
    assert parsed["origin"] == ["FACETED_SEARCH"]
    assert "date_posted" not in url


def test_posts_flutter_developer_remote_only():
    url = linkedin_posts_search_url(_task(work_mode="remote"))
    parsed = parse_qs(urlparse(url).query)

    assert parsed["keywords"] == [f'hiring "{_FLUTTER_ROLE}" remote {_COUNTRY}']
    assert parsed["datePosted"] == ['["past-week"]']
    assert parsed["sortBy"] == ['["relevance"]']
    assert parsed["origin"] == ["FACETED_SEARCH"]
