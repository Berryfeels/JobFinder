from __future__ import annotations

import pytest

from job_finder.fetchers.base import BaseFetcher


class _ConcreteFetcher(BaseFetcher):
    source_name = "test_source"

    def fetch(self, **kwargs):
        return []


@pytest.mark.unit
def test_base_fetcher_normalize_output_sets_source():
    fetcher = _ConcreteFetcher()
    raw = {"source_id": "r-1", "title": "Dev", "company": "co"}
    out = fetcher._normalize_output(raw)
    assert out["source"] == "test_source"
    assert out["source_id"] == "r-1"
    assert out["tags"] == []


@pytest.mark.unit
def test_base_fetcher_normalize_output_missing_source_id():
    """Missing source_id should default to empty string."""
    fetcher = _ConcreteFetcher()
    out = fetcher._normalize_output({"title": "Dev"})
    assert out["source_id"] == ""
