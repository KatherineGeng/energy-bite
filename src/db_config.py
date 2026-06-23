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


def _project_ref() -> str:
    ref = _secret("SUPABASE_PROJECT_REF")
    if ref:
        return ref
    host = _secret("SUPABASE_DB_HOST")
    if host.startswith("db.") and host.endswith(".supabase.co"):
        return host.removeprefix("db.").removesuffix(".supabase.co")
    return ""


def _build_url(*, host: str, port: str, user: str, password: str, dbname: str) -> str:
    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{dbname}?sslmode=require"
    )


@lru_cache(maxsize=1)
def get_database_urls() -> tuple[str, ...]:
    """Candidate DSNs — pooler first (required for Streamlit Cloud)."""
    password = _secret("SUPABASE_DB_PASSWORD")
    if not password:
        full = _secret("SUPABASE_DB_URL")
        return (full,) if full else ()

    dbname = _secret("SUPABASE_DB_NAME") or "postgres"
    urls: list[str] = []

    full = _secret("SUPABASE_DB_URL")
    if full:
        urls.append(full)

    pooler_host = _secret("SUPABASE_DB_POOLER_HOST")
    ref = _project_ref()
    if pooler_host:
        pool_user = _secret("SUPABASE_DB_USER")
        if not pool_user or pool_user == "postgres":
            pool_user = f"postgres.{ref}" if ref else "postgres"
        pool_port = _secret("SUPABASE_DB_POOLER_PORT") or "6543"
        urls.append(_build_url(host=pooler_host, port=pool_port, user=pool_user, password=password, dbname=dbname))

    host = _secret("SUPABASE_DB_HOST")
    if host:
        user = _secret("SUPABASE_DB_USER") or "postgres"
        port = _secret("SUPABASE_DB_PORT") or "5432"
        urls.append(_build_url(host=host, port=port, user=user, password=password, dbname=dbname))

    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return tuple(out)


def postgres_enabled() -> bool:
    return bool(get_database_urls())


def get_database_url() -> str:
    urls = get_database_urls()
    return urls[0] if urls else ""
