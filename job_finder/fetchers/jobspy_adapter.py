from __future__ import annotations

from typing import Any

from job_finder.fetchers.base import BaseFetcher

try:
    from jobspy import scrape_jobs
except ImportError:
    scrape_jobs = None


class JobSpyAdapter(BaseFetcher):
    source_name = "jobspy"

    def fetch(self, search_term: str, location: str = "", sites: list[str] | None = None, **kwargs) -> list[dict[str, Any]]:
        if not scrape_jobs:
            print("jobspy not installed")
            return []

        sites = sites or ["linkedin", "indeed", "glassdoor", "google"]
        try:
            df = scrape_jobs(
                site_name=sites,
                search_term=search_term,
                location=location,
                results_wanted=kwargs.get("results_wanted", 50),
                hours_old=kwargs.get("hours_old", 72),
            )
            jobs = []
            for _, row in df.iterrows():
                job_data = {
                    "source_id": str(row.get("job_url", "").split("/")[-1][:50]),
                    "title": row.get("title"),
                    "company": row.get("company"),
                    "location": row.get("location"),
                    "remote": bool(row.get("is_remote")),
                    "salary_min": int(row["min_amount"]) if row.get("min_amount") else None,
                    "salary_max": int(row["max_amount"]) if row.get("max_amount") else None,
                    "salary_currency": row.get("currency", "USD"),
                    "url": row.get("job_url"),
                    "email": row.get("emails", [None])[0] if row.get("emails") else None,
                    "description": row.get("description"),
                    "posted_at": str(row.get("date_posted")) if row.get("date_posted") else None,
                    "industry": row.get("company_industry"),
                }
                jobs.append(self._normalize_output(job_data))
            return jobs
        except Exception as e:
            print(f"JobSpy error: {e}")
            return []
