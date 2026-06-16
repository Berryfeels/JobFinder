from __future__ import annotations

import streamlit as st

from job_finder.config import load_config
from job_finder.core.search_engine import SearchEngine
from job_finder.db.database import get_session
from job_finder.ui.components.job_table import clear_cached_jobs


def render_search(user_id: str):
    """Render search page."""
    st.header("🔍 Search")

    config = load_config()
    session = get_session()

    supported_sources = [
        "linkedin",
        "indeed",
        "glassdoor",
        "google",
        "greenhouse",
        "lever",
        "adzuna",
        "arbeitnow",
    ]
    default_sources = [
        source
        for source in config.get("profiles", {}).get("tech", {}).get("sources_default", [])
        if source in supported_sources
    ] or ["linkedin", "indeed", "glassdoor"]

    tech_profile = config.get("profiles", {}).get("tech", {})
    scrape_keywords = ", ".join(tech_profile.get("keywords_default", []))

    st.caption(f"Scraping keywords from profile: {scrape_keywords or 'none'}")

    with st.form("search_form"):
        filter_keywords = st.text_area(
            "Filter keywords (comma-separated)",
            value="",
            help="Only jobs matching all entered keywords are kept and saved.",
        )

        sources = st.multiselect(
            "Sources",
            options=supported_sources,
            default=default_sources,
        )

        if st.form_submit_button("🔍 Search Now"):
            with st.spinner("Searching..."):
                search_engine = SearchEngine(session, user_id, profile_type="tech")
                result = search_engine.search(filter_keywords=filter_keywords, sources=sources)
                clear_cached_jobs(user_id)

                st.success(
                    f"✅ Scraped {result['total_scraped']} jobs, kept {result['total_found']} matching jobs, {result['new_jobs']} new"
                )

                if result["errors"]:
                    st.warning(f"⚠️ {len(result['errors'])} sources had errors")
                    for error in result["errors"]:
                        st.error(f"  {error['source']}: {error['error']}")
