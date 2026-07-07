"""Tests for LinkedIn search URL builders."""

from worker.linkedin_urls import with_current_job_id


def test_with_current_job_id_adds_query_param():
    base = (
        "https://www.linkedin.com/jobs/search/?keywords=AI+Engineer"
        "&location=Pakistan&f_TPR=r604800&sortBy=R"
    )
    url = with_current_job_id(base, "4437143380")
    assert "currentJobId=4437143380" in url
    assert "keywords=AI+Engineer" in url
