from __future__ import annotations

import pytest

import job_finder.core.search_engine as search_engine
from job_finder.core.search_engine import SearchEngine
from job_finder.db.models import Job, Search
from job_finder.fetchers.adzuna import AdzunaFetcher
from job_finder.fetchers.arbeitnow import ArbeitnowFetcher
from job_finder.fetchers.reliefweb import ReliefWebFetcher
from job_finder.fetchers.remotive import RemotiveFetcher
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


@pytest.mark.integration
def test_search_engine_records_error_when_fetcher_raises(monkeypatch, db_session, user_id):
    """If a fetcher raises, the error should be captured and search should continue."""
    config = {
        "profiles": {"tech": {"sources_default": ["greenhouse"]}},
        "slug_companies": ["acme"],
    }
    monkeypatch.setattr(search_engine, "load_config", lambda: config)
    monkeypatch.setattr(search_engine, "get_slug_companies", lambda _: ["acme"])

    def bad_fetch(self, **_kwargs):
        raise ConnectionError("timeout")

    monkeypatch.setattr(GreenhouseFetcher, "fetch", bad_fetch)

    engine = SearchEngine(db_session, user_id)
    result = engine.search("python")

    assert result["total_found"] == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["source"] == "greenhouse"
    assert result["errors"][0]["recoverable"] is True


@pytest.mark.integration
def test_search_engine_empty_companies_returns_zero(monkeypatch, db_session, user_id):
    """When no slug companies are configured, greenhouse/lever return 0 jobs."""
    config = {
        "profiles": {"tech": {"sources_default": ["greenhouse", "lever"]}},
        "slug_companies": [],
    }
    monkeypatch.setattr(search_engine, "load_config", lambda: config)
    monkeypatch.setattr(search_engine, "get_slug_companies", lambda _: [])

    engine = SearchEngine(db_session, user_id)
    result = engine.search("devops")

    assert result["total_found"] == 0
    assert result["new_jobs"] == 0


@pytest.mark.integration
def test_search_engine_jobspy_source(monkeypatch, db_session, user_id):
    """JobSpy source should be dispatched correctly and jobs saved."""
    import job_finder.fetchers.jobspy_adapter as jobspy_mod
    from job_finder.fetchers.jobspy_adapter import JobSpyAdapter

    config = {
        "profiles": {"tech": {"sources_default": ["linkedin"]}},
        "slug_companies": [],
        "jobspy": {"results_wanted": 10, "hours_old": 48},
    }
    monkeypatch.setattr(search_engine, "load_config", lambda: config)
    monkeypatch.setattr(search_engine, "get_slug_companies", lambda _: [])

    def fake_fetch(self, **kwargs):
        return [
            {
                "source": "jobspy",
                "source_id": "li-999",
                "company": "LinkedIn Corp",
                "title": "ML Engineer",
            }
        ]

    monkeypatch.setattr(JobSpyAdapter, "fetch", fake_fetch)

    engine = SearchEngine(db_session, user_id)
    result = engine.search("machine learning", location="Berlin")

    assert result["new_jobs"] == 1
    assert result["total_found"] == 1


@pytest.mark.integration
def test_search_engine_keyword_api_sources(monkeypatch, db_session, user_id):
    config = {
        "profiles": {"tech": {"sources_default": ["adzuna", "reliefweb", "remotive", "arbeitnow"]}},
        "api_keys": {"adzuna_app_id": "id", "adzuna_app_key": "key"},
        "adzuna": {"country": "de"},
    }
    monkeypatch.setattr(search_engine, "load_config", lambda: config)
    monkeypatch.setattr(search_engine, "get_slug_companies", lambda _: [])

    monkeypatch.setattr(
        AdzunaFetcher,
        "fetch",
        lambda self, **_kwargs: [{"source": "adzuna", "source_id": "a1", "company": "adz", "title": "A"}],
    )
    monkeypatch.setattr(
        ReliefWebFetcher,
        "fetch",
        lambda self, **_kwargs: [{"source": "reliefweb", "source_id": "r1", "company": "relief", "title": "B"}],
    )
    monkeypatch.setattr(
        RemotiveFetcher,
        "fetch",
        lambda self, **_kwargs: [{"source": "remotive", "source_id": "m1", "company": "rem", "title": "C"}],
    )
    monkeypatch.setattr(
        ArbeitnowFetcher,
        "fetch",
        lambda self, **_kwargs: [{"source": "arbeitnow", "source_id": "w1", "company": "arb", "title": "D"}],
    )

    engine = SearchEngine(db_session, user_id)
    result = engine.search("python")

    assert result["total_found"] == 4
    assert result["new_jobs"] == 4


@pytest.mark.integration
def test_search_engine_adzuna_missing_keys(monkeypatch, db_session, user_id):
    config = {
        "profiles": {"tech": {"sources_default": ["adzuna"]}},
        "api_keys": {"adzuna_app_id": "", "adzuna_app_key": ""},
    }
    monkeypatch.setattr(search_engine, "load_config", lambda: config)
    monkeypatch.setattr(search_engine, "get_slug_companies", lambda _: [])

    engine = SearchEngine(db_session, user_id)
    result = engine.search("python")

    assert result["total_found"] == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["source"] == "adzuna"
