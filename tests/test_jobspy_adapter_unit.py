from __future__ import annotations

import pandas as pd
import pytest

import job_finder.fetchers.jobspy_adapter as jobspy_adapter
from job_finder.fetchers.jobspy_adapter import JobSpyAdapter


@pytest.mark.unit
def test_jobspy_adapter_transforms_rows(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "job_url": "https://example.com/job/123",
                "title": "Python Engineer",
                "company": "acme",
                "location": "Berlin",
                "is_remote": True,
                "min_amount": 60000,
                "max_amount": 80000,
                "currency": "EUR",
                "emails": ["hr@example.com"],
                "description": "Great role",
                "date_posted": "2024-01-01",
                "company_industry": "Software",
            }
        ]
    )

    def fake_scrape_jobs(**_kwargs):
        return df

    monkeypatch.setattr(jobspy_adapter, "scrape_jobs", fake_scrape_jobs)
    jobs = JobSpyAdapter().fetch(search_term="python")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "jobspy"
    assert jobs[0]["salary_min"] == 60000
    assert jobs[0]["salary_max"] == 80000
    assert jobs[0]["email"] == "hr@example.com"


@pytest.mark.edge
def test_jobspy_adapter_handles_missing_dependency(monkeypatch):
    monkeypatch.setattr(jobspy_adapter, "scrape_jobs", None)
    jobs = JobSpyAdapter().fetch(search_term="python")
    assert jobs == []
