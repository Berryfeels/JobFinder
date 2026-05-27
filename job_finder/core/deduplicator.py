from __future__ import annotations

from sqlalchemy.orm import Session

from job_finder.db.models import Job


class Deduplicator:
    @staticmethod
    def is_duplicate(session: Session, user_id: str, source: str, source_id: str) -> bool:
        """Check if job already exists by (user_id, source, source_id)."""
        existing = session.query(Job).filter(
            Job.user_id == user_id,
            Job.source == source,
            Job.source_id == source_id,
        ).first()
        return existing is not None

    @staticmethod
    def is_similar_duplicate(session: Session, user_id: str, company: str, title: str, location: str) -> bool:
        """Fuzzy check for similar jobs from different sources."""
        if not (company and title):
            return False
        existing = session.query(Job).filter(
            Job.user_id == user_id,
            Job.company == company,
            Job.title == title,
            Job.location == location,
        ).first()
        return existing is not None
