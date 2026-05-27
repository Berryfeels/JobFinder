from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from job_finder.config import get_slug_companies, load_config
from job_finder.core.deduplicator import Deduplicator
from job_finder.core.normalizer import Normalizer
from job_finder.db.models import Job, Search
from job_finder.fetchers.slug_fetcher import GreenhouseFetcher, LeverFetcher
from job_finder.fetchers.jobspy_adapter import JobSpyAdapter


class SearchEngine:
    def __init__(self, session: Session, user_id: str):
        self.session = session
        self.user_id = user_id
        self.config = load_config()
        self.errors = []

    def search(
        self,
        keywords: str,
        location: str = "",
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Execute search across all sources."""
        sources = sources or self.config.get("profiles", {}).get("tech", {}).get("sources_default", [])
        jobs_found = []
        total_found = 0
        new_count = 0

        for source in sources:
            try:
                if source == "greenhouse":
                    jobs_found.extend(self._search_greenhouse())
                elif source == "lever":
                    jobs_found.extend(self._search_lever())
                elif source in ["linkedin", "indeed", "glassdoor", "google"]:
                    jobs_found.extend(self._search_jobspy([source], keywords, location))
            except Exception as e:
                self.errors.append({
                    "source": source,
                    "error": str(e),
                    "recoverable": True,
                })

        for job_data in jobs_found:
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
        total_found = len(jobs_found)

        search_record = Search(
            user_id=self.user_id,
            keywords=keywords,
            sources=",".join(sources),
            results_count=total_found,
        )
        self.session.add(search_record)
        self.session.commit()

        return {
            "total_found": total_found,
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
        location: str,
    ) -> list[dict[str, Any]]:
        fetcher = JobSpyAdapter()
        return fetcher.fetch(
            search_term=keywords,
            location=location,
            sites=sites,
            results_wanted=self.config.get("jobspy", {}).get("results_wanted", 50),
            hours_old=self.config.get("jobspy", {}).get("hours_old", 72),
        )

