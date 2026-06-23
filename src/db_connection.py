"""PostgreSQL connection helper for Supabase — reuse one connection per session."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
import psycopg2.extras
import streamlit as st

from src.db_config import get_database_urls, postgres_enabled

_CONN_KEY = "_pg_conn"


def pg_connect():
    if not postgres_enabled():
        raise RuntimeError("PostgreSQL is not configured")
    conn = st.session_state.get(_CONN_KEY)
    if conn is not None and not conn.closed:
        return conn
    last_error: Exception | None = None
    for url in get_database_urls():
        try:
            conn = psycopg2.connect(url, connect_timeout=10)
            st.session_state[_CONN_KEY] = conn
            return conn
        except psycopg2.OperationalError as exc:
            last_error = exc
    raise last_error or RuntimeError("Could not connect to PostgreSQL")


@contextmanager
def pg_cursor(*, dict_rows: bool = True) -> Iterator[Any]:
    conn = pg_connect()
    factory = psycopg2.extras.RealDictCursor if dict_rows else None
    cur = conn.cursor(cursor_factory=factory)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def pg_reset_connection() -> None:
    conn = st.session_state.pop(_CONN_KEY, None)
    if conn is not None and not conn.closed:
        try:
            conn.close()
        except Exception:
            pass
