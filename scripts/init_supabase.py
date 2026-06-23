#!/usr/bin/env python3
"""Apply supabase/schema.sql and seed global menu catalog."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db_config import get_database_url, postgres_enabled
from src.pg_store import init_postgres_schema, seed_global_catalog


def main() -> None:
    if not postgres_enabled():
        print("ERROR: Set SUPABASE_DB_URL or SUPABASE_DB_HOST + SUPABASE_DB_PASSWORD in secrets/env.")
        sys.exit(1)
    url = get_database_url()
    safe = url.split("@")[-1] if "@" in url else "(hidden)"
    print(f"Connecting to ...@{safe}")
    init_postgres_schema()
    print("Schema applied.")
    seed_global_catalog()
    print("Seed catalog ready.")


if __name__ == "__main__":
    main()
