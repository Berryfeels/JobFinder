from __future__ import annotations

import streamlit as st

from job_finder.db.database import get_session
from job_finder.ui.components.job_table import get_cached_jobs, render_job_section


def render_dashboard(user_id: str):
    """Render results dashboard."""
    st.header("📋 Results")

    session = get_session()
    jobs = get_cached_jobs(session, user_id)

    if not jobs:
        st.info("No jobs found yet. Run a search from the Search tab.")
        return

    st.subheader(f"✨ {len(jobs)} Jobs Found")

    cols = st.columns(3)
    cols[0].metric("Total", len(jobs))
    applied = len([j for j in jobs if j.application_sent])
    cols[1].metric("Applied", applied)
    new = len([j for j in jobs if j.status == "new"])
    cols[2].metric("New", new)

    st.divider()

    new_jobs = [j for j in jobs if j.status == "new"]
    if new_jobs:
        render_job_section(
            title="⚫ New Today",
            section_key="new",
            jobs=new_jobs,
            user_id=user_id,
            session=session,
            page_size=12,
            empty_message="No new jobs on this page.",
        )

    st.divider()
    interesting = [j for j in jobs if j.status == "saved"]
    if interesting:
        render_job_section(
            title="🟢 Interesting",
            section_key="saved",
            jobs=interesting,
            user_id=user_id,
            session=session,
            page_size=12,
            empty_message="No interesting jobs on this page.",
        )
