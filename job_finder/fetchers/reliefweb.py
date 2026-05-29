from __future__ import annotations

from typing import Any

import httpx

from job_finder.fetchers.base import BaseFetcher
from job_finder.fetchers.keyword_fetcher import normalize_keywords


class ReliefWebFetcher(BaseFetcher):
    source_name = "reliefweb"
    BASE_URL = "https://api.reliefweb.int/v1/jobs"

    def __init__(self, limit: int = 50, appname: str = "jobfinder"):
        self.limit = limit
        self.appname = appname

    def fetch(self, keywords: str, **_kwargs) -> list[dict[str, Any]]:
        query = normalize_keywords(keywords)
        params = {
            "appname": self.appname,
            "limit": self.limit,
        }
        if query:
            params["query[value]"] = query

        response = httpx.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        jobs = []
        for item in payload.get("data", []):
            fields = item.get("fields") or {}
            date_info = fields.get("date") if isinstance(fields.get("date"), dict) else {}
            job_data = {
                "source_id": str(item.get("id") or fields.get("id") or ""),
                "title": fields.get("title"),
                "company": _first_name(fields.get("source")),
                "location": _format_location(fields.get("city"), fields.get("country")),
                "url": fields.get("url") or item.get("href"),
                "description": fields.get("body") or fields.get("description"),
                "tags": _extract_names(fields.get("theme")),
                "posted_at": date_info.get("created") or date_info.get("changed"),
                "raw_data": item,
            }
            jobs.append(self._normalize_output(job_data))
        return jobs


def _first_name(value: Any) -> str | None:
    names = _extract_names(value)
    return names[0] if names else None


def _extract_names(value: Any) -> list[str]:
    if isinstance(value, list):
        names = []
        for entry in value:
            if isinstance(entry, dict):
                name = entry.get("name")
                if name:
                    names.append(name)
            elif isinstance(entry, str):
                names.append(entry)
        return names
    if isinstance(value, dict):
        name = value.get("name")
        return [name] if name else []
    if isinstance(value, str):
        return [value]
    return []


def _format_location(city: Any, country: Any) -> str | None:
    city_names = _extract_names(city)
    if city_names:
        return ", ".join(city_names)
    country_names = _extract_names(country)
    return ", ".join(country_names) if country_names else None
