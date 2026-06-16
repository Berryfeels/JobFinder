from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from job_finder.config import get_profile_defaults, load_config
from job_finder.core.search_engine import SearchEngine
from job_finder.db.database import get_session
from job_finder.db.queries import get_user_by_username

logging.basicConfig(filename="jobfinder.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def run_search_for_user(username: str):
    """Run search for a specific user."""
    config = load_config()
    session = get_session()
    user = get_user_by_username(session, username)

    if not user:
        logger.warning(f"User {username} not found")
        return

    profile = get_profile_defaults(config, user.profile_type or "tech")

    logger.info(f"Starting search for user {username}")

    search_engine = SearchEngine(session, user.id, profile_type=user.profile_type or "tech")
    result = search_engine.search(
        filter_keywords="",
        sources=profile.get("sources", []),
    )

    logger.info(
        f"Search complete: scraped {result['total_scraped']} jobs, kept {result['total_found']} matching jobs, {result['new_jobs']} new"
    )


def start_scheduler():
    """Start the background scheduler."""
    config = load_config()
    scheduler = BackgroundScheduler()

    default_time = config.get("scheduler", {}).get("default_time", "08:00")
    hour, minute = map(int, default_time.split(":"))

    scheduler.add_job(
        func=run_search_for_user,
        args=("admin",),
        trigger="cron",
        hour=hour,
        minute=minute,
        id="daily_search",
    )

    scheduler.start()
    logger.info(f"Scheduler started. Daily search at {default_time}")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    start_scheduler()
