from __future__ import annotations

from datetime import datetime

import pytest

from job_finder.db.queries import (
    get_job_by_source,
    get_or_create_user,
    mark_application_sent,
    save_job,
    update_job_status,
)
from job_finder.db.models import Job


@pytest.mark.integration
def test_get_or_create_user_creates_new(db_session):
    user = get_or_create_user(db_session, "newuser", email="new@example.com")
    assert user.id is not None
    assert user.username == "newuser"


@pytest.mark.integration
def test_get_or_create_user_is_idempotent(db_session):
    u1 = get_or_create_user(db_session, "alice")
    u2 = get_or_create_user(db_session, "alice")
    assert u1.id == u2.id


@pytest.mark.integration
def test_save_job_persists(db_session, user_id):
    job_data = {
        "user_id": user_id,
        "source": "greenhouse",
        "source_id": "saved-1",
        "company": "SaveCo",
        "title": "DevOps",
        "status": "new",
    }
    job = save_job(db_session, job_data)
    assert job.id is not None
    fetched = get_job_by_source(db_session, user_id, "greenhouse", "saved-1")
    assert fetched is not None
    assert fetched.title == "DevOps"


@pytest.mark.integration
def test_update_job_status(db_session, user_id):
    job = Job(
        user_id=user_id, source="lever", source_id="upd-1",
        company="X", title="PM", status="new",
    )
    db_session.add(job)
    db_session.commit()

    updated = update_job_status(db_session, job.id, "reviewing", notes="Looks good")
    assert updated.status == "reviewing"
    assert updated.notes == "Looks good"


@pytest.mark.integration
def test_update_job_status_unknown_id_returns_none(db_session):
    assert update_job_status(db_session, "nonexistent-id", "applied") is None


@pytest.mark.integration
def test_mark_application_sent(db_session, user_id):
    """
    BUG DOCUMENTATO: mark_application_sent riceve `date` come stringa,
    ma Job.application_date è mappato come DateTime in SQLAlchemy.
    Passare una stringa causa StatementError su SQLite (e probabilmente
    anche su PostgreSQL).  Il fix corretto è convertire la stringa in
    datetime prima dell'assegnazione, oppure cambiare il tipo della
    colonna a String.  Fino ad allora il test usa un datetime object.
    """
    job = Job(
        user_id=user_id, source="greenhouse", source_id="app-1",
        company="Y", title="SRE", status="new",
    )
    db_session.add(job)
    db_session.commit()

    app_date = datetime(2024, 5, 1)
    result = mark_application_sent(db_session, job.id, app_date)
    assert result.application_sent is True
    assert result.status == "applied"
    assert result.application_date == app_date


@pytest.mark.integration
def test_get_job_by_source_not_found(db_session, user_id):
    assert get_job_by_source(db_session, user_id, "greenhouse", "ghost") is None
