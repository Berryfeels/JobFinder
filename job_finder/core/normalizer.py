from __future__ import annotations

import json
from datetime import datetime
from typing import Any


class Normalizer:
    """Normalize fetcher output to DB-ready format."""

    @staticmethod
    def normalize(fetcher_data: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Convert fetcher output to database format."""
        return {
            "user_id": user_id,
            "source": fetcher_data.get("source", "unknown"),
            "source_id": fetcher_data.get("source_id", ""),
            "company": fetcher_data.get("company"),
            "company_slug": fetcher_data.get("company_slug"),
            "title": fetcher_data.get("title"),
            "industry": fetcher_data.get("industry"),
            "location": fetcher_data.get("location"),
            "remote": fetcher_data.get("remote"),
            "salary_min": fetcher_data.get("salary_min"),
            "salary_max": fetcher_data.get("salary_max"),
            "salary_currency": fetcher_data.get("salary_currency"),
            "contract_type": fetcher_data.get("contract_type"),
            "url": fetcher_data.get("url"),
            "email": fetcher_data.get("email"),
            "phone": fetcher_data.get("phone"),
            "description": fetcher_data.get("description"),
            "raw_data": json.dumps(fetcher_data.get("raw_data", {})),
            "tags": json.dumps(fetcher_data.get("tags", [])),
            "posted_at": Normalizer._parse_datetime(fetcher_data.get("posted_at")),
            "fetched_at": datetime.utcnow(),
            "status": "new",
        }

    @staticmethod
    def _parse_datetime(dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            if isinstance(dt_str, str):
                if "T" in dt_str:
                    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                return datetime.strptime(dt_str[:10], "%Y-%m-%d")
            return dt_str
        except Exception:
            return None
