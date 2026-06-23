"""PostgreSQL connection helper for Supabase."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
import psycopg2.extras

from src.db_config import get_database_url, postgres_enabled


@contextmanager
def pg_cursor(*, dict_rows: bool = True) -> Iterator[Any]:
    if not postgres_enabled():
        raise RuntimeError("PostgreSQL is not configured")
    url = get_database_url()
    conn = psycopg2.connect(url)
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
