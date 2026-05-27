from __future__ import annotations

import streamlit as st

from job_finder.config import load_config
from job_finder.db.database import get_session
from job_finder.db.queries import get_or_create_user


def render_login():
    config = load_config()
    creds = config.get("auth", {}).get("credentials", {}).get("usernames", {})

    st.title("🔐 Job Finder Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin123")
        submit = st.form_submit_button("✅ Login")
        
        if submit:
            st.write(f"DEBUG: Checking {username} against {list(creds.keys())}")
            
            if username not in creds:
                st.error(f"User '{username}' not found")
                return None
            
            stored_pass = creds[username].get("password")
            st.write(f"DEBUG: Comparing '{password}' with '{stored_pass}'")
            
            if password == stored_pass:
                session = get_session()
                user = get_or_create_user(session, username, profile_type="tech")
                st.session_state["user_id"] = user.id
                st.session_state["authenticated"] = True
                st.success(f"✅ Welcome {username}!")
            else:
                st.error("❌ Wrong password")
                return None

    if st.session_state.get("authenticated"):
        return st.session_state.get("user_id")
    
    st.caption(f"DEBUG session_state: {dict(st.session_state)}")
    return None
