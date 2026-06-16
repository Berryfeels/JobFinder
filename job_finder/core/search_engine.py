from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from job_finder.config import get_profile_defaults, get_slug_companies, load_config
from job_finder.core.deduplicator import Deduplicator
from job_finder.core.normalizer import Normalizer
from job_finder.db.models import Job, Search
from job_finder.fetchers.adzuna import AdzunaFetcher
from job_finder.fetchers.arbeitnow import ArbeitnowFetcher
from job_finder.fetchers.jobspy_adapter import JobSpyAdapter
from job_finder.fetchers.keyword_fetcher import keyword_tokens, matches_keywords
from job_finder.fetchers.remotive import RemotiveFetcher
from job_finder.fetchers.slug_fetcher import GreenhouseFetcher, LeverFetcher


class SearchEngine:
    def __init__(self, session: Session, user_id: str, profile_type: str = "tech"):
        self.session = session
        self.user_id = user_id
        self.config = load_config()
        self.profile_defaults = get_profile_defaults(self.config, profile_type)
        self.errors = []

    def search(
        self,
        filter_keywords: str = "",
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Execute search across all sources."""
        scrape_keywords = ", ".join(self.profile_defaults.get("keywords", []))
        resolved_sources = sources or self.profile_defaults.get("sources", [])
        if not isinstance(resolved_sources, list):
            resolved_sources = list(resolved_sources or [])
        jobs_found: list[dict[str, Any]] = []
        kept_jobs: list[dict[str, Any]] = []
        total_scraped = 0
        new_count = 0
        filter_tokens = keyword_tokens(filter_keywords)

        for source in resolved_sources:
            try:
                if source == "greenhouse":
                    jobs_found.extend(self._search_greenhouse())
                elif source == "lever":
                    jobs_found.extend(self._search_lever())
                elif source == "adzuna":
                    jobs_found.extend(self._search_adzuna(scrape_keywords))
                elif source == "remotive":
                    jobs_found.extend(self._search_remotive(scrape_keywords))
                elif source == "arbeitnow":
                    jobs_found.extend(self._search_arbeitnow(scrape_keywords))
                elif source in ["linkedin", "indeed", "glassdoor", "google"]:
                    jobs_found.extend(self._search_jobspy([source], scrape_keywords))
            except Exception as e:
                self.errors.append({
                    "source": source,
                    "error": str(e),
                    "recoverable": True,
                })

        total_scraped = len(jobs_found)

        for job_data in jobs_found:
            if not _matches_filter(job_data, filter_tokens):
                continue

            kept_jobs.append(job_data)
            normalized = Normalizer.normalize(job_data, self.user_id)
            if not Deduplicator.is_duplicate(
                self.session,
                self.user_id,
                normalized["source"],
                normalized["source_id"],
            ):
                try:
                    job = Job(**normalized)
                    self.session.add(job)
                    new_count += 1
                except Exception as e:
                    print(f"Error saving job: {e}")

        self.session.commit()

        search_record = Search(
            user_id=self.user_id,
            keywords=filter_keywords,
            sources=",".join(resolved_sources),
            results_count=len(kept_jobs),
        )
        self.session.add(search_record)
        self.session.commit()

        return {
            "total_scraped": total_scraped,
            "total_found": len(kept_jobs),
            "new_jobs": new_count,
            "errors": self.errors,
        }

    def _search_greenhouse(self) -> list[dict[str, Any]]:
        companies = get_slug_companies(self.config)
        if not companies:
            return []
        fetcher = GreenhouseFetcher(companies)
        return fetcher.fetch()

    def _search_lever(self) -> list[dict[str, Any]]:
        companies = get_slug_companies(self.config)
        if not companies:
            return []
        fetcher = LeverFetcher(companies)
        return fetcher.fetch()

    def _search_jobspy(
        self,
        sites: list[str],
        keywords: str,
    ) -> list[dict[str, Any]]:
        fetcher = JobSpyAdapter()
        return fetcher.fetch(
            search_term=keywords,
            location="",
            sites=sites,
            results_wanted=self.config.get("jobspy", {}).get("results_wanted", 50),
            hours_old=self.config.get("jobspy", {}).get("hours_old", 72),
        )

    def _search_adzuna(self, keywords: str) -> list[dict[str, Any]]:
        api_keys = self.config.get("api_keys", {})
        app_id = api_keys.get("adzuna_app_id")
        app_key = api_keys.get("adzuna_app_key")
        country = self.config.get("adzuna", {}).get("country", "de")
        results_per_page = self.config.get("adzuna", {}).get("results_per_page", 50)
        fetcher = AdzunaFetcher(
            app_id=app_id,
            app_key=app_key,
            country=country,
            results_per_page=results_per_page,
        )
        return fetcher.fetch(keywords=keywords)

    def _search_remotive(self, keywords: str) -> list[dict[str, Any]]:
        limit = self.config.get("remotive", {}).get("limit", 50)
        fetcher = RemotiveFetcher(limit=limit)
        return fetcher.fetch(keywords=keywords)

    def _search_arbeitnow(self, keywords: str) -> list[dict[str, Any]]:
        limit = self.config.get("arbeitnow", {}).get("limit")
        fetcher = ArbeitnowFetcher(limit=limit)
        return fetcher.fetch(keywords=keywords, location="")


def _matches_filter(job_data: dict[str, Any], filter_tokens: list[str]) -> bool:
    if not filter_tokens:
        return True

    searchable_parts: list[str] = []
    for key in ("title", "company", "location", "description", "industry"):
        value = job_data.get(key)
        if isinstance(value, str) and value.strip():
            searchable_parts.append(value)

    tags = job_data.get("tags") or []
    if isinstance(tags, list):
        searchable_parts.extend(tag for tag in tags if isinstance(tag, str) and tag.strip())

    return matches_keywords(" ".join(searchable_parts), filter_tokens)
