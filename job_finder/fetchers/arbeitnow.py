from __future__ import annotations

from typing import Any

import httpx

from job_finder.fetchers.base import BaseFetcher
from job_finder.fetchers.keyword_fetcher import keyword_tokens, matches_keywords, normalize_keywords


class ArbeitnowFetcher(BaseFetcher):
    source_name = "arbeitnow"
    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    def __init__(self, limit: int | None = None):
        self.limit = limit

    def fetch(self, keywords: str, location: str = "", **_kwargs) -> list[dict[str, Any]]:
        query = normalize_keywords(keywords)
        params: dict[str, Any] = {}
        if query:
            params["search"] = query
        if location:
            params["location"] = location

        response = httpx.get(self.BASE_URL, params=params or None, timeout=10)
        response.raise_for_status()
        payload = response.json()

        tokens = keyword_tokens(keywords)
        jobs = []
        for job in payload.get("data", []):
            if tokens and not _matches_job(job, tokens):
                continue
            job_data = {
                "source_id": job.get("slug") or job.get("url") or "",
                "title": job.get("title"),
                "company": job.get("company_name"),
                "location": job.get("location"),
                "remote": job.get("remote"),
                "contract_type": _first_job_type(job.get("job_types")),
                "url": job.get("url"),
                "description": job.get("description"),
                "tags": job.get("tags") or [],
                "posted_at": job.get("created_at"),
                "raw_data": job,
            }
            jobs.append(self._normalize_output(job_data))

        if self.limit:
            return jobs[: self.limit]
        return jobs


def _first_job_type(value: Any) -> str | None:
    if isinstance(value, list) and value:
        return value[0]
    if isinstance(value, str):
        return value
    return None


def _matches_job(job: dict[str, Any], tokens: list[str]) -> bool:
    haystack = " ".join(
        part
        for part in [
            job.get("title"),
            job.get("description"),
            job.get("company_name"),
        ]
        if isinstance(part, str)
    )
    return matches_keywords(haystack, tokens)
