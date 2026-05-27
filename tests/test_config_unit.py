from __future__ import annotations

import pytest

from job_finder.config import get_profile_defaults, get_slug_companies


@pytest.mark.unit
def test_get_profile_defaults_known_profile():
    config = {
        "profiles": {
            "tech": {
                "keywords_default": ["python"],
                "location_default": "Berlin",
                "remote": True,
                "sources_default": ["greenhouse"],
            }
        }
    }
    defaults = get_profile_defaults(config, "tech")
    assert defaults["keywords"] == ["python"]
    assert defaults["location"] == "Berlin"
    assert defaults["remote"] is True
    assert defaults["sources"] == ["greenhouse"]


@pytest.mark.unit
def test_get_profile_defaults_unknown_falls_back_to_tech():
    config = {
        "profiles": {
            "tech": {"keywords_default": ["go"], "sources_default": ["lever"]}
        }
    }
    defaults = get_profile_defaults(config, "geopolitics")
    assert defaults["sources"] == ["lever"]


@pytest.mark.unit
def test_get_slug_companies_empty():
    assert get_slug_companies({}) == []


@pytest.mark.unit
def test_get_slug_companies_returns_list():
    config = {"slug_companies": ["acme", "startup"]}
    assert get_slug_companies(config) == ["acme", "startup"]
