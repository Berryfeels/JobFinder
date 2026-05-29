from __future__ import annotations

import streamlit as st

from job_finder.config import load_config
from job_finder.core.search_engine import SearchEngine
from job_finder.db.database import get_session


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
        "reliefweb",
        "remotive",
        "arbeitnow",
    ]
    default_sources = [
        source
        for source in config.get("profiles", {}).get("tech", {}).get("sources_default", [])
        if source in supported_sources
    ] or ["linkedin", "indeed", "glassdoor"]

    with st.form("search_form"):
        keywords = st.text_area("Keywords (comma-separated)", value="software engineer, python, backend")
        location = st.text_input("Location", value="Berlin, Germany")
        remote_only = st.checkbox("Remote only", value=True)

        sources = st.multiselect(
            "Sources",
            options=supported_sources,
            default=default_sources,
        )

        if st.form_submit_button("🔍 Search Now"):
            with st.spinner("Searching..."):
                search_engine = SearchEngine(session, user_id)
                result = search_engine.search(keywords, location, sources)

                st.success(f"✅ Found {result['total_found']} jobs, {result['new_jobs']} new")

                if result["errors"]:
                    st.warning(f"⚠️ {len(result['errors'])} sources had errors")
                    for error in result["errors"]:
                        st.error(f"  {error['source']}: {error['error']}")
