from __future__ import annotations

import pytest

from job_finder.core.deduplicator import Deduplicator
from job_finder.db.models import Job


@pytest.mark.unit
def test_is_duplicate_detects_existing(db_session, user_id):
    job = Job(
        user_id=user_id,
        source="greenhouse",
        source_id="abc",
        company="acme",
        title="Engineer",
    )
    db_session.add(job)
    db_session.commit()

    assert Deduplicator.is_duplicate(db_session, user_id, "greenhouse", "abc") is True
    assert Deduplicator.is_duplicate(db_session, user_id, "greenhouse", "xyz") is False


@pytest.mark.unit
def test_is_similar_duplicate_detects_match(db_session, user_id):
    """is_similar_duplicate should return True when company+title+location match."""
    job = Job(
        user_id=user_id,
        source="greenhouse",
        source_id="dup-99",
        company="acme",
        title="Senior Engineer",
        location="Berlin",
    )
    db_session.add(job)
    db_session.commit()

    assert Deduplicator.is_similar_duplicate(db_session, user_id, "acme", "Senior Engineer", "Berlin") is True


@pytest.mark.edge
def test_is_similar_duplicate_requires_company_and_title(db_session, user_id):
    assert Deduplicator.is_similar_duplicate(db_session, user_id, "", "Engineer", "Berlin") is False
    assert Deduplicator.is_similar_duplicate(db_session, user_id, "acme", "", "Berlin") is False


@pytest.mark.edge
def test_is_similar_duplicate_empty_location_still_matches(db_session, user_id):
    """Location can be an empty string — the function should still query the DB."""
    job = Job(
        user_id=user_id,
        source="lever",
        source_id="dup-100",
        company="beta",
        title="QA Engineer",
        location="",
    )
    db_session.add(job)
    db_session.commit()

    assert Deduplicator.is_similar_duplicate(db_session, user_id, "beta", "QA Engineer", "") is True


@pytest.mark.edge
def test_is_similar_duplicate_no_match_different_location(db_session, user_id):
    """Same company+title but different location should NOT be a duplicate."""
    job = Job(
        user_id=user_id,
        source="greenhouse",
        source_id="dup-101",
        company="acme",
        title="DevOps",
        location="London",
    )
    db_session.add(job)
    db_session.commit()

    assert Deduplicator.is_similar_duplicate(db_session, user_id, "acme", "DevOps", "Berlin") is False

