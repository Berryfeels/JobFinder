from __future__ import annotations

import pytest

import job_finder.fetchers.adzuna as adzuna_mod
import job_finder.fetchers.arbeitnow as arbeitnow_mod
import job_finder.fetchers.reliefweb as reliefweb_mod
import job_finder.fetchers.remotive as remotive_mod
from job_finder.fetchers.adzuna import AdzunaFetcher
from job_finder.fetchers.arbeitnow import ArbeitnowFetcher
from job_finder.fetchers.reliefweb import ReliefWebFetcher
from job_finder.fetchers.remotive import RemotiveFetcher


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.mark.unit
def test_adzuna_fetcher_parses_jobs(monkeypatch):
    payload = {
        "results": [
            {
                "id": 123,
                "title": "Backend Engineer",
                "company": {"display_name": "Acme"},
                "location": {"display_name": "Berlin"},
                "salary_min": 50000,
                "salary_max": 70000,
                "salary_currency": "EUR",
                "contract_time": "full_time",
                "redirect_url": "https://example.com/job/123",
                "description": "Great role",
                "category": {"label": "Software"},
                "created": "2024-01-01T00:00:00Z",
            }
        ]
    }

    def fake_get(url, params=None, timeout=10):
        return DummyResponse(payload)

    monkeypatch.setattr(adzuna_mod.httpx, "get", fake_get)
    fetcher = AdzunaFetcher(app_id="id", app_key="key", country="de")
    jobs = fetcher.fetch(keywords="python", location="Berlin")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "adzuna"
    assert jobs[0]["company"] == "Acme"
    assert jobs[0]["salary_min"] == 50000


@pytest.mark.unit
def test_adzuna_fetcher_requires_keys():
    fetcher = AdzunaFetcher(app_id="", app_key="")
    with pytest.raises(ValueError):
        fetcher.fetch(keywords="python")


@pytest.mark.unit
def test_reliefweb_fetcher_parses_jobs(monkeypatch):
    payload = {
        "data": [
            {
                "id": "rw-1",
                "fields": {
                    "title": "Policy Analyst",
                    "body": "Description",
                    "url": "https://reliefweb.int/job/1",
                    "source": [{"name": "UN"}],
                    "country": [{"name": "Germany"}],
                    "date": {"created": "2024-02-01T00:00:00Z"},
                    "theme": [{"name": "Humanitarian"}],
                },
            }
        ]
    }

    def fake_get(url, params=None, timeout=10):
        return DummyResponse(payload)

    monkeypatch.setattr(reliefweb_mod.httpx, "get", fake_get)
    fetcher = ReliefWebFetcher()
    jobs = fetcher.fetch(keywords="policy")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "reliefweb"
    assert jobs[0]["company"] == "UN"
    assert jobs[0]["location"] == "Germany"
    assert jobs[0]["tags"] == ["Humanitarian"]


@pytest.mark.unit
def test_remotive_fetcher_parses_jobs(monkeypatch):
    payload = {
        "jobs": [
            {
                "id": 456,
                "title": "Remote Engineer",
                "company_name": "RemoteCo",
                "candidate_required_location": "Anywhere",
                "job_type": "full_time",
                "url": "https://remotive.com/job/456",
                "description": "Remote role",
                "tags": ["python"],
                "publication_date": "2024-03-01T00:00:00Z",
                "category": "Software Development",
            }
        ]
    }

    def fake_get(url, params=None, timeout=10):
        return DummyResponse(payload)

    monkeypatch.setattr(remotive_mod.httpx, "get", fake_get)
    fetcher = RemotiveFetcher()
    jobs = fetcher.fetch(keywords="python")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "remotive"
    assert jobs[0]["remote"] is True
    assert jobs[0]["contract_type"] == "full_time"


@pytest.mark.unit
def test_arbeitnow_fetcher_parses_jobs(monkeypatch):
    payload = {
        "data": [
            {
                "slug": "job-1",
                "company_name": "Acme",
                "title": "Python Developer",
                "location": "Berlin",
                "remote": True,
                "job_types": ["Full-time"],
                "url": "https://arbeitnow.com/jobs/1",
                "description": "Python developer role",
                "tags": ["python"],
                "created_at": "2024-04-01T00:00:00Z",
            }
        ]
    }

    def fake_get(url, params=None, timeout=10):
        return DummyResponse(payload)

    monkeypatch.setattr(arbeitnow_mod.httpx, "get", fake_get)
    fetcher = ArbeitnowFetcher()
    jobs = fetcher.fetch(keywords="python", location="Berlin")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "arbeitnow"
    assert jobs[0]["company"] == "Acme"
