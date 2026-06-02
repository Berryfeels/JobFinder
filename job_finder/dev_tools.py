from __future__ import annotations

import argparse
import os
import sys

from job_finder.db.database import get_session
from job_finder.db.models import Job, Search
from job_finder.db.queries import get_user_by_username


def _ensure_dev_mode() -> None:
    if os.getenv("JOBFINDER_ENV", "").lower() != "dev":
        raise SystemExit("Dev-only command. Set JOBFINDER_ENV=dev to proceed.")


def _flush_search_results(username: str | None, include_searches: bool) -> None:
    session = get_session()
    try:
        user_id = None
        if username:
            user = get_user_by_username(session, username)
            if not user:
                raise SystemExit(f"User '{username}' not found.")
            user_id = user.id

        jobs_query = session.query(Job)
        searches_query = session.query(Search)
        if user_id:
            jobs_query = jobs_query.filter(Job.user_id == user_id)
            searches_query = searches_query.filter(Search.user_id == user_id)

        deleted_jobs = jobs_query.delete(synchronize_session=False)
        deleted_searches = 0
        if include_searches:
            deleted_searches = searches_query.delete(synchronize_session=False)

        session.commit()
    finally:
        session.close()

    scope = f"user '{username}'" if username else "all users"
    print(f"Deleted {deleted_jobs} jobs for {scope}.")
    if include_searches:
        print(f"Deleted {deleted_searches} search records for {scope}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="JobFinder dev-only tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    flush_parser = subparsers.add_parser(
        "flush-search-results",
        help="Delete all job results (and optionally search history).",
    )
    flush_parser.add_argument(
        "--user",
        help="Only delete results for this username.",
    )
    flush_parser.add_argument(
        "--include-searches",
        action="store_true",
        help="Also delete search history.",
    )
    flush_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm destructive action.",
    )

    args = parser.parse_args()
    _ensure_dev_mode()

    if args.command == "flush-search-results":
        if not args.yes:
            raise SystemExit("Refusing to run without --yes.")
        _flush_search_results(args.user, args.include_searches)
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
