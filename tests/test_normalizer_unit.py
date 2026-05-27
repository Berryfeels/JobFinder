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


@pytest.mark.edge
def test_parse_datetime_invalid_returns_none():
    assert Normalizer._parse_datetime("not-a-date") is None
