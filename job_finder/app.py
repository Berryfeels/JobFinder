from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure repository root is on sys.path when running `streamlit run job_finder/app.py`
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from job_finder.db.database import get_db_manager
from job_finder.ui.pages.login import render_login
from job_finder.ui.pages.dashboard import render_dashboard
from job_finder.ui.pages.search import render_search
from job_finder.ui.pages.settings import render_settings

st.set_page_config(page_title="Job Finder", layout="wide", initial_sidebar_state="expanded")

# Initialize DB
get_db_manager()

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Login or main app
if not st.session_state.get("authenticated"):
    user_id = render_login()
    if user_id:
        st.session_state["user_id"] = user_id
        st.rerun()
else:
    user_id = st.session_state.get("user_id")
    
    # Sidebar logout
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.get('username', 'Admin')}**")
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📋 Results", "🔍 Search", "⚙️ Account"])

    with tab1:
        render_dashboard(user_id)

    with tab2:
        render_search(user_id)

    with tab3:
        render_settings(user_id)
