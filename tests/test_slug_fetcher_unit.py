from __future__ import annotations

import pytest

import job_finder.fetchers.slug_fetcher as slug_fetcher
from job_finder.fetchers.slug_fetcher import GreenhouseFetcher, LeverFetcher


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.mark.unit
def test_greenhouse_fetcher_parses_jobs(monkeypatch):
    payload = {
        "jobs": [
            {
                "id": 1,
                "title": "Backend Engineer",
                "location": {"name": "Berlin"},
                "absolute_url": "https://example.com/job/1",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        ]
    }

    def fake_get(url, timeout=10):
        return DummyResponse(payload)

    monkeypatch.setattr(slug_fetcher.httpx, "get", fake_get)
    fetcher = GreenhouseFetcher(["acme"])
    jobs = fetcher.fetch()

    assert len(jobs) == 1
    assert jobs[0]["source"] == "greenhouse"
    assert jobs[0]["company"] == "acme"
    assert jobs[0]["title"] == "Backend Engineer"


@pytest.mark.unit
def test_lever_fetcher_parses_jobs(monkeypatch):
    payload = [
        {
            "id": "abc",
            "text": "Data Engineer",
            "categories": {"location": "Remote"},
            "hostedUrl": "https://example.com/job/abc",
            "createdAt": "2024-02-02T00:00:00Z",
        }
    ]

    def fake_get(url, params=None, timeout=10):
        return DummyResponse(payload)

    monkeypatch.setattr(slug_fetcher.httpx, "get", fake_get)
    fetcher = LeverFetcher(["acme"])
    jobs = fetcher.fetch()

    assert len(jobs) == 1
    assert jobs[0]["source"] == "lever"
    assert jobs[0]["company"] == "acme"
    assert jobs[0]["title"] == "Data Engineer"


@pytest.mark.edge
def test_fetcher_handles_http_errors(monkeypatch):
    def fake_get(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(slug_fetcher.httpx, "get", fake_get)
    fetcher = GreenhouseFetcher(["acme"])
    jobs = fetcher.fetch()

    assert jobs == []
