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


@pytest.mark.edge
def test_is_similar_duplicate_requires_company_and_title(db_session, user_id):
    assert Deduplicator.is_similar_duplicate(db_session, user_id, "", "Engineer", "Berlin") is False
    assert Deduplicator.is_similar_duplicate(db_session, user_id, "acme", "", "Berlin") is False
