"""PostgreSQL connection helper for Supabase."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
import psycopg2.extras

from src.db_config import get_database_urls, postgres_enabled


def pg_connect():
    if not postgres_enabled():
        raise RuntimeError("PostgreSQL is not configured")
    last_error: Exception | None = None
    for url in get_database_urls():
        try:
            return psycopg2.connect(url, connect_timeout=15)
        except psycopg2.OperationalError as exc:
            last_error = exc
    raise last_error or RuntimeError("Could not connect to PostgreSQL")


@contextmanager
def pg_cursor(*, dict_rows: bool = True) -> Iterator[Any]:
    conn = pg_connect()
    try:
        factory = psycopg2.extras.RealDictCursor if dict_rows else None
        with conn.cursor(cursor_factory=factory) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
