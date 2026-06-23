"""Supabase / PostgreSQL connection settings from Streamlit secrets or env."""

from __future__ import annotations

import os
from functools import lru_cache
from urllib.parse import quote_plus


def _secret(name: str) -> str:
    try:
        import streamlit as st

        val = st.secrets.get(name, "")
        if val:
            return str(val).strip()
    except Exception:
        pass
    return str(os.environ.get(name, "")).strip()


def postgres_enabled() -> bool:
    return bool(get_database_url())


@lru_cache(maxsize=1)
def get_database_url() -> str:
    direct = _secret("SUPABASE_DB_URL")
    if direct:
        return direct
    host = _secret("SUPABASE_DB_HOST")
    password = _secret("SUPABASE_DB_PASSWORD")
    if not host or not password:
        return ""
    user = _secret("SUPABASE_DB_USER") or "postgres"
    dbname = _secret("SUPABASE_DB_NAME") or "postgres"
    port = _secret("SUPABASE_DB_PORT") or "5432"
    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{dbname}?sslmode=require"
    )
