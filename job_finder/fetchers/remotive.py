from __future__ import annotations

from typing import Any

import httpx

from job_finder.fetchers.base import BaseFetcher
from job_finder.fetchers.keyword_fetcher import normalize_keywords


class RemotiveFetcher(BaseFetcher):
    source_name = "remotive"
    BASE_URL = "https://remotive.com/api/remote-jobs"

    def __init__(self, limit: int = 50):
        self.limit = limit

    def fetch(self, keywords: str, **_kwargs) -> list[dict[str, Any]]:
        query = normalize_keywords(keywords)
        params: dict[str, Any] = {"limit": self.limit}
        if query:
            params["search"] = query

        response = httpx.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        jobs = []
        for job in payload.get("jobs", []):
            job_data = {
                "source_id": str(job.get("id") or job.get("url") or ""),
                "title": job.get("title"),
                "company": job.get("company_name"),
                "location": job.get("candidate_required_location"),
                "remote": True,
                "contract_type": job.get("job_type"),
                "url": job.get("url"),
                "description": job.get("description"),
                "tags": job.get("tags") or [],
                "posted_at": job.get("publication_date"),
                "industry": job.get("category"),
                "raw_data": job,
            }
            jobs.append(self._normalize_output(job_data))
        return jobs
