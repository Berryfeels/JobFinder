from __future__ import annotations

import json
from datetime import datetime

import pytest

from job_finder.core.normalizer import Normalizer


@pytest.mark.unit
def test_normalize_basic_fields():
    payload = {
        "source": "greenhouse",
        "source_id": "123",
        "company": "acme",
        "company_slug": "acme",
        "title": "Backend Engineer",
        "location": "Berlin",
        "url": "https://example.com/job/123",
        "posted_at": "2024-01-15T10:30:00Z",
        "raw_data": {"id": 123},
        "tags": ["python", "api"],
    }

    result = Normalizer.normalize(payload, user_id="user-1")

    assert result["user_id"] == "user-1"
    assert result["source"] == "greenhouse"
    assert result["source_id"] == "123"
    assert result["company"] == "acme"
    assert result["company_slug"] == "acme"
    assert result["title"] == "Backend Engineer"
    assert result["location"] == "Berlin"
    assert result["url"] == "https://example.com/job/123"
    assert isinstance(result["posted_at"], datetime)
    assert json.loads(result["raw_data"]) == {"id": 123}
    assert json.loads(result["tags"]) == ["python", "api"]


@pytest.mark.unit
def test_normalizer_salary_and_remote_fields():
    """Salary and remote flag should pass through."""
    payload = {
        "source": "jobspy",
        "source_id": "j-1",
        "company": "TechCorp",
        "title": "Data Scientist",
        "salary_min": 70000,
        "salary_max": 90000,
        "salary_currency": "EUR",
        "remote": True,
    }
    result = Normalizer.normalize(payload, user_id="u-1")
    assert result["salary_min"] == 70000
    assert result["salary_max"] == 90000
    assert result["salary_currency"] == "EUR"
    assert result["remote"] is True


@pytest.mark.unit
def test_normalizer_missing_source_id_defaults_to_empty():
    """source_id not in payload should default to empty string."""
    payload = {"source": "greenhouse", "company": "x", "title": "Eng"}
    result = Normalizer.normalize(payload, user_id="u-2")
    assert result["source_id"] == ""


@pytest.mark.unit
def test_normalizer_null_tags_and_raw_data():
    """tags and raw_data should be serialised to JSON-safe defaults when absent."""
    payload = {"source": "lever", "source_id": "l-1"}
    result = Normalizer.normalize(payload, user_id="u-3")
    assert json.loads(result["tags"]) == []
    assert json.loads(result["raw_data"]) == {}


@pytest.mark.unit
def test_normalizer_status_is_new():
    """Every normalised job should have status='new'."""
    result = Normalizer.normalize({"source": "x", "source_id": "1"}, user_id="u-4")
    assert result["status"] == "new"


@pytest.mark.edge
def test_parse_datetime_invalid_returns_none():
    assert Normalizer._parse_datetime("not-a-date") is None


@pytest.mark.unit
def test_parse_datetime_date_only_string():
    """'YYYY-MM-DD' format should be parsed correctly."""
    dt = Normalizer._parse_datetime("2024-06-15")
    assert isinstance(dt, datetime)
    assert dt.year == 2024
    assert dt.month == 6
    assert dt.day == 15


@pytest.mark.unit
def test_parse_datetime_none_returns_none():
    assert Normalizer._parse_datetime(None) is None


@pytest.mark.unit
def test_parse_datetime_iso_with_z():
    """ISO 8601 string ending in 'Z' should parse without error."""
    dt = Normalizer._parse_datetime("2024-03-20T08:00:00Z")
    assert isinstance(dt, datetime)


@pytest.mark.unit
def test_parse_datetime_already_datetime_passthrough():
    """If the value is already a datetime, it should be returned as-is."""
    now = datetime(2024, 1, 1)
    assert Normalizer._parse_datetime(now) == now

