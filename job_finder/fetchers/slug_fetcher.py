from __future__ import annotations

from typing import Any

import httpx

from job_finder.fetchers.base import BaseFetcher


class GreenhouseFetcher(BaseFetcher):
    source_name = "greenhouse"
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, slugs: list[str]):
        self.slugs = slugs

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        jobs = []
        for slug in self.slugs:
            try:
                jobs.extend(self._fetch_for_slug(slug))
            except Exception as e:
                print(f"Error fetching Greenhouse slug {slug}: {e}")
        return jobs

    def _fetch_for_slug(self, slug: str) -> list[dict[str, Any]]:
        url = f"{self.BASE_URL}/{slug}/jobs"
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for job in data.get("jobs", []):
            job_data = {
                "source_id": str(job.get("id", "")),
                "title": job.get("title"),
                "company": slug,
                "company_slug": slug,
                "location": job.get("location", {}).get("name") if job.get("location") else None,
                "url": job.get("absolute_url"),
                "posted_at": job.get("updated_at"),
            }
            jobs.append(self._normalize_output(job_data))
        return jobs


class LeverFetcher(BaseFetcher):
    source_name = "lever"
    BASE_URL = "https://api.lever.co/v0/postings"

    def __init__(self, slugs: list[str]):
        self.slugs = slugs

    def fetch(self, **kwargs) -> list[dict[str, Any]]:
        jobs = []
        for slug in self.slugs:
            try:
                jobs.extend(self._fetch_for_slug(slug))
            except Exception as e:
                print(f"Error fetching Lever slug {slug}: {e}")
        return jobs

    def _fetch_for_slug(self, slug: str) -> list[dict[str, Any]]:
        url = f"{self.BASE_URL}/{slug}"
        response = httpx.get(url, params={"mode": "json"}, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for posting in data:
            job_data = {
                "source_id": str(posting.get("id", "")),
                "title": posting.get("text"),
                "company": slug,
                "company_slug": slug,
                "location": posting.get("categories", {}).get("location") if posting.get("categories") else None,
                "url": posting.get("hostedUrl"),
                "posted_at": posting.get("createdAt"),
            }
            jobs.append(self._normalize_output(job_data))
        return jobs
