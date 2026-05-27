from __future__ import annotations

import pytest

import job_finder.core.search_engine as search_engine
from job_finder.core.search_engine import SearchEngine
from job_finder.db.queries import get_jobs_for_user
from job_finder.fetchers.slug_fetcher import GreenhouseFetcher


@pytest.mark.e2e
def test_end_to_end_search_flow(monkeypatch, db_session, user_id):
    config = {
        "profiles": {"tech": {"sources_default": ["greenhouse"]}},
        "slug_companies": ["acme"],
    }

    monkeypatch.setattr(search_engine, "load_config", lambda: config)
    monkeypatch.setattr(search_engine, "get_slug_companies", lambda _config: ["acme"])

    def gh_fetch(self, **_kwargs):
        return [
            {
                "source": "greenhouse",
                "source_id": "42",
                "company": "acme",
                "title": "Platform Engineer",
                "location": "Remote",
            }
        ]

    monkeypatch.setattr(GreenhouseFetcher, "fetch", gh_fetch)

    engine = SearchEngine(db_session, user_id)
    engine.search("platform")

    jobs = get_jobs_for_user(db_session, user_id)
    assert len(jobs) == 1
    assert jobs[0].title == "Platform Engineer"
