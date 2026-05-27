from __future__ import annotations

import pytest

import job_finder.core.search_engine as search_engine
from job_finder.core.search_engine import SearchEngine
from job_finder.db.models import Job, Search
from job_finder.fetchers.slug_fetcher import GreenhouseFetcher, LeverFetcher


@pytest.mark.integration
def test_search_engine_inserts_jobs_and_search_record(monkeypatch, db_session, user_id):
    config = {
        "profiles": {"tech": {"sources_default": ["greenhouse", "lever"]}},
        "slug_companies": ["acme"],
    }

    monkeypatch.setattr(search_engine, "load_config", lambda: config)
    monkeypatch.setattr(search_engine, "get_slug_companies", lambda _config: ["acme"])

    def gh_fetch(self, **_kwargs):
        return [
            {
                "source": "greenhouse",
                "source_id": "1",
                "company": "acme",
                "title": "Backend Engineer",
            }
        ]

    def lv_fetch(self, **_kwargs):
        return [
            {
                "source": "lever",
                "source_id": "2",
                "company": "acme",
                "title": "Data Engineer",
            }
        ]

    monkeypatch.setattr(GreenhouseFetcher, "fetch", gh_fetch)
    monkeypatch.setattr(LeverFetcher, "fetch", lv_fetch)

    engine = SearchEngine(db_session, user_id)
    result = engine.search("python")

    assert result["total_found"] == 2
    assert result["new_jobs"] == 2

    jobs = db_session.query(Job).filter_by(user_id=user_id).all()
    assert len(jobs) == 2

    searches = db_session.query(Search).all()
    assert len(searches) == 1
    assert searches[0].sources == "greenhouse,lever"


@pytest.mark.integration
def test_search_engine_skips_duplicates(monkeypatch, db_session, user_id):
    config = {
        "profiles": {"tech": {"sources_default": ["greenhouse"]}},
        "slug_companies": ["acme"],
    }

    monkeypatch.setattr(search_engine, "load_config", lambda: config)
    monkeypatch.setattr(search_engine, "get_slug_companies", lambda _config: ["acme"])

    def gh_fetch(self, **_kwargs):
        return [
            {"source": "greenhouse", "source_id": "1", "company": "acme", "title": "Backend Engineer"},
            {"source": "greenhouse", "source_id": "1", "company": "acme", "title": "Backend Engineer"},
        ]

    monkeypatch.setattr(GreenhouseFetcher, "fetch", gh_fetch)

    engine = SearchEngine(db_session, user_id)
    result = engine.search("python")

    assert result["total_found"] == 2
    assert result["new_jobs"] == 1
