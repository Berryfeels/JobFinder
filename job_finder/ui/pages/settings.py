from __future__ import annotations

import streamlit as st

from job_finder.db.database import get_session


def render_settings(user_id: str):
    """Render settings page."""
    st.header("⚙️ Account Settings")

    session = get_session()
    user = session.query(__import__("job_finder.db.models", fromlist=["User"]).User).filter_by(id=user_id).first()

    if user:
        st.write(f"**Username:** {user.username}")
        st.write(f"**Email:** {user.email}")
        st.write(f"**Profile:** {user.profile_type}")

        if st.button("🚪 Logout", key="logout_settings"):
            st.session_state.clear()
            st.rerun()
