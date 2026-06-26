"""Poster bytes — session cache + optional Postgres snapshot."""

from __future__ import annotations

import base64
from typing import Any

import streamlit as st


def _cache() -> dict[str, bytes]:
    if "poster_cache" not in st.session_state:
        st.session_state.poster_cache = {}
    return st.session_state.poster_cache


def _decode_b64(stored: str | None) -> bytes | None:
    if not stored:
        return None
    try:
        return base64.b64decode(stored.encode("ascii"))
    except Exception:
        return None


def _store_b64(date_str: str, png_bytes: bytes) -> None:
    st.session_state.poster_b64 = base64.b64encode(png_bytes).decode("ascii")
    b64_cache = dict(st.session_state.get("poster_b64_cache") or {})
    b64_cache[date_str] = st.session_state.poster_b64
    st.session_state.poster_b64_cache = b64_cache


def save_poster_state(date_str: str, png_bytes: bytes, menu_ids: list[str]) -> None:
    st.session_state.poster_bytes = png_bytes
    st.session_state.poster_filename = f"jianyu_{date_str}.png"
    st.session_state.poster_menu_ids = list(menu_ids)
    st.session_state.poster_date_str = date_str
    st.session_state.poster_last_generated = date_str
    if "poster_share_text" not in st.session_state:
        st.session_state.poster_share_text = ""

    cache = dict(_cache())
    cache[date_str] = png_bytes
    st.session_state.poster_cache = cache
    _store_b64(date_str, png_bytes)

    from src.db_config import postgres_enabled

    if postgres_enabled():
        from src.pg_store import pg_save_poster_snapshot

        pg_save_poster_snapshot(date_str, png_bytes, menu_ids)


def _apply_cached(date_str: str, png_bytes: bytes, menu_ids: list[str] | None = None) -> None:
    st.session_state.poster_bytes = png_bytes
    st.session_state.poster_filename = f"jianyu_{date_str}.png"
    st.session_state.poster_date_str = date_str
    st.session_state.poster_last_generated = date_str
    if menu_ids is not None:
        st.session_state.poster_menu_ids = menu_ids
    _store_b64(date_str, png_bytes)


def _load_from_postgres(date_str: str) -> tuple[bytes, list[str]] | None:
    from src.db_config import postgres_enabled

    if not postgres_enabled():
        return None
    from src.pg_store import pg_load_poster_snapshot

    return pg_load_poster_snapshot(date_str)


def _restore_candidates(preferred_date: str | None) -> list[str]:
    candidates: list[str] = []
    for key in ("poster_last_generated", "poster_date_str"):
        val = st.session_state.get(key)
        if val and str(val) not in candidates:
            candidates.append(str(val))
    if preferred_date and preferred_date not in candidates:
        candidates.append(preferred_date)
    for item in st.session_state.get("poster_history") or []:
        d = str(item.get("date") or "")
        if d and d not in candidates:
            candidates.append(d)
    for date_str in sorted(_cache().keys(), reverse=True):
        if date_str not in candidates:
            candidates.append(date_str)
    return candidates


def restore_poster_for_display(preferred_date: str | None = None) -> bool:
    """Load poster_bytes from session / cache / Postgres when hero is empty."""
    if st.session_state.get("poster_bytes"):
        return True

    b64 = st.session_state.get("poster_b64")
    if b64:
        decoded = _decode_b64(b64)
        if decoded:
            date_str = str(st.session_state.get("poster_date_str") or st.session_state.get("poster_last_generated") or "")
            _apply_cached(date_str or "unknown", decoded)
            return True

    cache = _cache()
    b64_cache = dict(st.session_state.get("poster_b64_cache") or {})

    for date_str in _restore_candidates(preferred_date):
        if date_str in cache:
            _apply_cached(date_str, cache[date_str])
            return True
        if date_str in b64_cache:
            decoded = _decode_b64(b64_cache[date_str])
            if decoded:
                _apply_cached(date_str, decoded)
                cache[date_str] = decoded
                st.session_state.poster_cache = cache
                return True
        loaded = _load_from_postgres(date_str)
        if loaded:
            png_bytes, menu_ids = loaded
            _apply_cached(date_str, png_bytes, menu_ids)
            cache[date_str] = png_bytes
            st.session_state.poster_cache = cache
            return True
    return False


def user_has_generated_poster() -> bool:
    if st.session_state.get("poster_bytes"):
        return True
    if st.session_state.get("poster_last_generated"):
        return True
    if st.session_state.get("poster_b64"):
        return True
    if _cache():
        return True
    if st.session_state.get("poster_history"):
        return True
    return False


def all_menu_ids_for_poster(date_str: str) -> list[str]:
    """Full confirmed menu in meal-slot order (早餐→午餐→晚餐, all dishes)."""
    from src.database import load_daily_meal_plan
    from src.meal_plan_utils import flatten_plan

    saved = load_daily_meal_plan(date_str)
    if saved and saved.get("plan"):
        ids = flatten_plan(saved["plan"])
        if ids:
            return [str(x) for x in ids]

    from src.session_hydrate import menu_ids_for_date

    ids = menu_ids_for_date(date_str)
    if ids:
        return list(ids)
    return list(st.session_state.get("final_daily_list") or st.session_state.get("current_day_menus") or [])


def meals_for_poster(date_str: str, menu_ids: list[str]) -> list[dict[str, Any]]:
    from src.database import get_menu_row, load_daily_meal_plan

    plan = load_daily_meal_plan(date_str)
    snapshots: dict[str, dict[str, str]] = {}
    if plan:
        snapshots = dict(plan.get("snapshots") or {})
    if not snapshots:
        snapshots = dict(st.session_state.get("eb_plan_snapshots") or {})

    use_ids = all_menu_ids_for_poster(date_str) or list(menu_ids)

    meals: list[dict[str, Any]] = []
    for menu_id in use_ids:
        row = get_menu_row(menu_id, snapshots)
        if row:
            meals.append(row)
    return meals
