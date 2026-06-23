"""Poster bytes — session cache + optional Postgres snapshot."""

from __future__ import annotations

from typing import Any

import streamlit as st


def _cache() -> dict[str, bytes]:
    if "poster_cache" not in st.session_state:
        st.session_state.poster_cache = {}
    return st.session_state.poster_cache


def save_poster_state(date_str: str, png_bytes: bytes, menu_ids: list[str]) -> None:
    st.session_state.poster_bytes = png_bytes
    st.session_state.poster_filename = f"jianyu_{date_str}.png"
    st.session_state.poster_menu_ids = list(menu_ids)
    st.session_state.poster_date_str = date_str
    if "poster_share_text" not in st.session_state:
        st.session_state.poster_share_text = ""

    cache = dict(_cache())
    cache[date_str] = png_bytes
    st.session_state.poster_cache = cache

    from src.db_config import postgres_enabled

    if postgres_enabled():
        from src.pg_store import pg_save_poster_snapshot

        pg_save_poster_snapshot(date_str, png_bytes, menu_ids)


def restore_poster_for_display(preferred_date: str | None = None) -> bool:
    """Load poster_bytes from session cache or Postgres when hero is empty."""
    if st.session_state.get("poster_bytes"):
        return True

    cache = _cache()
    candidates: list[str] = []
    if preferred_date:
        candidates.append(preferred_date)
    saved = st.session_state.get("poster_date_str")
    if saved and saved not in candidates:
        candidates.append(str(saved))
    for date_str in sorted(cache.keys(), reverse=True):
        if date_str not in candidates:
            candidates.append(date_str)

    for date_str in candidates:
        if date_str in cache:
            _apply_cached(date_str, cache[date_str])
            return True
        loaded = _load_from_postgres(date_str)
        if loaded:
            png_bytes, menu_ids = loaded
            _apply_cached(date_str, png_bytes, menu_ids)
            cache[date_str] = png_bytes
            st.session_state.poster_cache = cache
            return True
    return False


def _apply_cached(date_str: str, png_bytes: bytes, menu_ids: list[str] | None = None) -> None:
    st.session_state.poster_bytes = png_bytes
    st.session_state.poster_filename = f"jianyu_{date_str}.png"
    st.session_state.poster_date_str = date_str
    if menu_ids is not None:
        st.session_state.poster_menu_ids = menu_ids


def _load_from_postgres(date_str: str) -> tuple[bytes, list[str]] | None:
    from src.db_config import postgres_enabled

    if not postgres_enabled():
        return None
    from src.pg_store import pg_load_poster_snapshot

    return pg_load_poster_snapshot(date_str)


def meals_for_poster(date_str: str, menu_ids: list[str]) -> list[dict[str, Any]]:
    from src.database import get_menu_row, load_daily_meal_plan

    plan = load_daily_meal_plan(date_str)
    snapshots: dict[str, dict[str, str]] = {}
    if plan:
        snapshots = dict(plan.get("snapshots") or {})
    if not snapshots:
        snapshots = dict(st.session_state.get("eb_plan_snapshots") or {})

    meals: list[dict[str, Any]] = []
    for menu_id in menu_ids:
        row = get_menu_row(menu_id, snapshots)
        if row:
            meals.append(row)
    return meals
