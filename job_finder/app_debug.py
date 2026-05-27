from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure repository root is on sys.path when running `streamlit run job_finder/app_debug.py`
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from job_finder.ui.pages.login_debug import render_login
from job_finder.ui.pages.dashboard import render_dashboard
from job_finder.ui.pages.search import render_search
from job_finder.ui.pages.settings import render_settings
from job_finder.db.database import get_db_manager

st.set_page_config(page_title="Job Finder", layout="wide")

get_db_manager()

if "user_id" not in st.session_state:
    user_id = render_login()
    if user_id:
        st.session_state["user_id"] = user_id
        st.rerun()
else:
    user_id = st.session_state["user_id"]
    tab1, tab2, tab3 = st.tabs(["📋 Results", "🔍 Search", "⚙️ Account"])

    with tab1:
        render_dashboard(user_id)

    with tab2:
        render_search(user_id)

    with tab3:
        render_settings(user_id)
