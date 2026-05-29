from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseFetcher(ABC):
    source_name: str

    @abstractmethod
    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch jobs and return standard format."""
        pass

    def _normalize_output(self, raw_job: dict) -> dict[str, Any]:
        """Return dict with guaranteed schema."""
        return {
            "source": self.source_name,
            "source_id": raw_job.get("source_id", ""),
            "raw_data": raw_job.get("raw_data", raw_job),
            "title": raw_job.get("title"),
            "company": raw_job.get("company"),
            "location": raw_job.get("location"),
            "remote": raw_job.get("remote"),
            "salary_min": raw_job.get("salary_min"),
            "salary_max": raw_job.get("salary_max"),
            "salary_currency": raw_job.get("salary_currency"),
            "contract_type": raw_job.get("contract_type"),
            "url": raw_job.get("url"),
            "email": raw_job.get("email"),
            "phone": raw_job.get("phone"),
            "description": raw_job.get("description"),
            "industry": raw_job.get("industry"),
            "tags": raw_job.get("tags") or [],
            "posted_at": raw_job.get("posted_at"),
        }
