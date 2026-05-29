from __future__ import annotations

from typing import Any

import httpx

from job_finder.fetchers.base import BaseFetcher
from job_finder.fetchers.keyword_fetcher import normalize_keywords


class AdzunaFetcher(BaseFetcher):
    source_name = "adzuna"
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        country: str = "de",
        results_per_page: int = 50,
    ):
        self.app_id = app_id
        self.app_key = app_key
        self.country = country
        self.results_per_page = results_per_page

    def fetch(self, keywords: str, location: str = "", **_kwargs) -> list[dict[str, Any]]:
        if not self.app_id or not self.app_key:
            raise ValueError("Adzuna API keys missing")

        query = normalize_keywords(keywords)
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query,
            "results_per_page": self.results_per_page,
        }
        if location:
            params["where"] = location

        url = f"{self.BASE_URL}/{self.country}/search/1"
        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        jobs = []
        for job in payload.get("results", []):
            job_data = {
                "source_id": str(job.get("id") or job.get("adref") or job.get("redirect_url") or ""),
                "title": job.get("title"),
                "company": _extract_company(job.get("company")),
                "location": _extract_location(job.get("location")),
                "salary_min": _coerce_int(job.get("salary_min")),
                "salary_max": _coerce_int(job.get("salary_max")),
                "salary_currency": job.get("salary_currency"),
                "contract_type": job.get("contract_time") or job.get("contract_type"),
                "url": job.get("redirect_url") or job.get("ad_url"),
                "description": job.get("description"),
                "industry": _extract_category(job.get("category")),
                "tags": _extract_tags(job.get("category")),
                "posted_at": job.get("created"),
                "raw_data": job,
            }
            jobs.append(self._normalize_output(job_data))
        return jobs


def _extract_company(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("display_name") or value.get("name")
    if isinstance(value, str):
        return value
    return None


def _extract_location(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("display_name") or value.get("name")
    if isinstance(value, str):
        return value
    return None


def _extract_category(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get("label") or value.get("tag")
    if isinstance(value, str):
        return value
    return None


def _extract_tags(value: Any) -> list[str]:
    tag = _extract_category(value)
    return [tag] if tag else []


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
