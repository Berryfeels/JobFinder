from __future__ import annotations

import streamlit as st
import streamlit_authenticator as stauth

from job_finder.config import load_config
from job_finder.db.database import get_session
from job_finder.db.queries import get_or_create_user


def _build_authenticator(config: dict) -> stauth.Authenticate:
    auth_config = config.get("auth", {})
    credentials = auth_config.get("credentials", {})
    cookie_name = auth_config.get("cookie_name", "job_finder_auth")
    secret_key = auth_config.get("secret_key", "dev-secret-key")
    cookie_expiry_days = auth_config.get("cookie_expiry_days", 7)
    return stauth.Authenticate(
        credentials,
        cookie_name,
        secret_key,
        cookie_expiry_days,
    )


def render_login() -> str | None:
    config = load_config()
    authenticator = _build_authenticator(config)

    _, authentication_status, username = authenticator.login("🔐 Job Finder Login", "main")

    if authentication_status:
        user_info = (
            config.get("auth", {})
            .get("credentials", {})
            .get("usernames", {})
            .get(username, {})
        )
        session = get_session()
        user = get_or_create_user(
            session,
            username=username,
            email=user_info.get("email", ""),
            profile_type=user_info.get("profile_type", "tech"),
        )
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        return user.id

    if authentication_status is False:
        st.error("Username/password incorrect")
    elif authentication_status is None:
        st.info("Please enter your username and password")

    return None
