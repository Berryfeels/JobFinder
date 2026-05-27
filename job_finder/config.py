from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

CONFIG_FILENAME = "config.yaml"


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or Path(__file__).with_name(CONFIG_FILENAME)
    config = yaml.safe_load(config_path.read_text()) or {}

    _apply_env_overrides(config)
    _ensure_passwords_hashed(config)
    return config


def _apply_env_overrides(config: dict[str, Any]) -> None:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        config.setdefault("database", {})["url"] = database_url

    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        config.setdefault("auth", {})["secret_key"] = secret_key

    adzuna_id = os.getenv("ADZUNA_APP_ID")
    adzuna_key = os.getenv("ADZUNA_APP_KEY")
    if adzuna_id or adzuna_key:
        api_keys = config.setdefault("api_keys", {})
        if adzuna_id:
            api_keys["adzuna_app_id"] = adzuna_id
        if adzuna_key:
            api_keys["adzuna_app_key"] = adzuna_key


def _ensure_passwords_hashed(config: dict[str, Any]) -> None:
    credentials = (
        config.get("auth", {})
        .get("credentials", {})
        .get("usernames", {})
    )
    if not credentials:
        return

    try:
        from streamlit_authenticator.utilities.hasher import Hasher
    except Exception:
        return

    for username, user in credentials.items():
        password = user.get("password")
        if not password or _is_bcrypt_hash(password):
            continue
        user["password"] = Hasher([password]).generate()[0]


def _is_bcrypt_hash(value: str) -> bool:
    return value.startswith("$2a$") or value.startswith("$2b$") or value.startswith("$2y$")


def get_profile_defaults(config: dict[str, Any], profile_type: str) -> dict[str, Any]:
    profiles = config.get("profiles", {})
    profile = profiles.get(profile_type) or profiles.get("tech") or {}
    return {
        "keywords": profile.get("keywords_default", []),
        "location": profile.get("location_default", ""),
        "remote": bool(profile.get("remote", False)),
        "sources": profile.get("sources_default", []),
    }


def get_slug_companies(config: dict[str, Any]) -> list[str]:
    return list(config.get("slug_companies", []) or [])
