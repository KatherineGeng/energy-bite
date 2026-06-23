"""Pytest defaults — unit tests use CSV backend, not Supabase."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _csv_backend_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.db_config.postgres_enabled", lambda: False)
