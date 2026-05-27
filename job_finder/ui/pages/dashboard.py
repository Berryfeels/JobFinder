from __future__ import annotations

import streamlit as st

from job_finder.db.database import get_session
from job_finder.db.queries import get_jobs_for_user, mark_application_sent, update_job_status


def render_dashboard(user_id: str):
    """Render results dashboard."""
    st.header("📋 Results")

    session = get_session()
    jobs = get_jobs_for_user(session, user_id)

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
        st.subheader("⚫ New Today")
        for job in new_jobs[:5]:
            with st.expander(f"🔹 {job.company} — {job.title}"):
                st.write(f"**Location:** {job.location or 'Remote'}")
                st.write(f"**Salary:** {job.salary_min or 'N/A'} - {job.salary_max or 'N/A'} {job.salary_currency or ''}")
                st.write(f"**Posted:** {job.posted_at}")
                if job.url:
                    st.markdown(f"[View Job]({job.url})")
                if job.description:
                    st.write("**Description:**")
                    st.write(job.description[:500])

                col1, col2 = st.columns(2)
                if col1.button("🟢 Interesting", key=f"int_{job.id}"):
                    update_job_status(session, job.id, "saved")
                    st.rerun()
                if col2.button("🔴 Not Interesting", key=f"not_{job.id}"):
                    update_job_status(session, job.id, "rejected")
                    st.rerun()

    st.divider()
    st.subheader("🟢 Interesting")
    interesting = [j for j in jobs if j.status == "saved"]
    if interesting:
        for job in interesting:
            with st.expander(f"🟢 {job.company} — {job.title}"):
                if job.url:
                    st.markdown(f"[View Job]({job.url})")
                col1, col2 = st.columns(2)
                if not job.application_sent and col1.button("✅ Mark Applied", key=f"app_{job.id}"):
                    mark_application_sent(session, job.id, str(st.date_input("Date applied", key=f"date_{job.id}")))
                    st.rerun()
                if col2.button("🔴 Not Interesting", key=f"ni_{job.id}"):
                    update_job_status(session, job.id, "rejected")
                    st.rerun()
