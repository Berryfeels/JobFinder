from __future__ import annotations

from sqlalchemy.orm import Session

from job_finder.db.models import Job, User


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.query(User).filter(User.username == username).first()


def get_or_create_user(session: Session, username: str, email: str = "", profile_type: str = "tech") -> User:
    user = get_user_by_username(session, username)
    if not user:
        user = User(username=username, email=email, profile_type=profile_type)
        session.add(user)
        session.commit()
    return user


def get_jobs_for_user(session: Session, user_id: str) -> list[Job]:
    return session.query(Job).filter(Job.user_id == user_id).order_by(Job.fetched_at.desc()).all()


def get_job_by_source(session: Session, user_id: str, source: str, source_id: str) -> Job | None:
    return session.query(Job).filter(
        Job.user_id == user_id,
        Job.source == source,
        Job.source_id == source_id,
    ).first()


def save_job(session: Session, job_data: dict) -> Job:
    job = Job(**job_data)
    session.add(job)
    session.commit()
    return job


def update_job_status(session: Session, job_id: str, status: str, notes: str = "") -> Job | None:
    job = session.query(Job).filter(Job.id == job_id).first()
    if job:
        job.status = status
        if notes:
            job.notes = notes
        session.commit()
    return job


def mark_application_sent(session: Session, job_id: str, date: str) -> Job | None:
    job = session.query(Job).filter(Job.id == job_id).first()
    if job:
        job.application_sent = True
        job.application_date = date
        job.status = "applied"
        session.commit()
    return job
