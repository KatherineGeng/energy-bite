"""Session date sync tests."""

from __future__ import annotations

import sys
from datetime import date as real_date
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.session_hydrate import sync_session_date


class _SessionState(dict):
    def get(self, key, default=None):
        return super().get(key, default)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]

    def pop(self, key, default=None):
        return super().pop(key, default)


def test_sync_session_date_clears_stale_day(monkeypatch):
    import src.app_time as at
    import src.session_hydrate as sh

    fake_state = _SessionState(
        today_date="2026-06-22",
        _hydrated_date="2026-06-22",
        meal_plan={"早餐": ["MENU_001"], "午餐": [], "晚餐": []},
        menu_locked=True,
    )
    monkeypatch.setattr(st, "session_state", fake_state)
    monkeypatch.setattr(at, "beijing_today", lambda: real_date(2026, 6, 23))
    monkeypatch.setattr(sh, "beijing_today_iso", lambda: "2026-06-23")

    today = sync_session_date()
    assert today == "2026-06-23"
    assert fake_state["today_date"] == "2026-06-23"
    assert fake_state.get("_hydrated_date") is None
    assert fake_state["menu_locked"] is False
    assert fake_state["meal_plan"] == {"早餐": [], "午餐": [], "晚餐": []}
