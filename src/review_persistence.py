"""Persist and restore morning + evening review state."""

from __future__ import annotations

import streamlit as st

from src.database import get_logs_for_date, load_review_draft, save_morning_context, save_review_draft

_MORNING_SIG_KEY = "eb_morning_disk_sig"


def mark_morning_disk_signature(today_iso: str, sleep: str, load: str, meal_count: int) -> None:
    st.session_state[_MORNING_SIG_KEY] = f"{today_iso}|{sleep}|{load}|{meal_count}"


def autosave_morning_context(today_iso: str) -> None:
    """Write morning three questions to DB when values change."""
    sleep = st.session_state.get("morning_sleep")
    load = st.session_state.get("morning_load")
    meal_count = st.session_state.get("morning_meal_count")
    if sleep is None or load is None or meal_count is None:
        return
    sig = f"{today_iso}|{sleep}|{load}|{meal_count}"
    if st.session_state.get(_MORNING_SIG_KEY) == sig:
        return
    save_morning_context(today_iso, str(sleep), str(load), int(meal_count))
    st.session_state.morning_inputs = {
        "sleep": str(sleep),
        "load": str(load),
        "meal_count": int(meal_count),
    }
    st.session_state.morning_context_loaded = today_iso
    mark_morning_disk_signature(today_iso, str(sleep), str(load), int(meal_count))


def review_day_submitted(day: str) -> bool:
    draft = load_review_draft(day)
    if draft and draft.get("completed"):
        return True
    return not get_logs_for_date(day).empty


def collect_review_draft_from_session(menu_ids: list[str]) -> dict:
    dishes: dict[str, dict] = {}
    for menu_id in menu_ids:
        operation = st.session_state.get(f"review_{menu_id}_operation")
        nps = st.session_state.get(f"review_{menu_id}_nps")
        favorited = st.session_state.get(f"review_{menu_id}_fav_dish")
        entry: dict = {}
        if operation is not None:
            entry["operation"] = int(operation)
        if nps is not None:
            entry["nps"] = int(nps)
        if favorited is not None:
            entry["favorited"] = bool(favorited)
        if entry:
            dishes[menu_id] = entry
    return {
        "day_mood": st.session_state.get("review_day_mood"),
        "day_energy": st.session_state.get("review_day_energy"),
        "fav_full_day": bool(st.session_state.get("review_fav_full_day", False)),
        "dishes": dishes,
        "completed": False,
    }


def apply_review_draft_to_session(day: str, menu_ids: list[str]) -> None:
    if review_day_submitted(day):
        return
    draft = load_review_draft(day)
    if not draft:
        return
    day_mood = draft.get("day_mood")
    if day_mood is not None:
        st.session_state.review_day_mood = int(day_mood)
    day_energy = draft.get("day_energy")
    if day_energy is not None:
        st.session_state.review_day_energy = int(day_energy)
    if "fav_full_day" in draft:
        st.session_state.review_fav_full_day = bool(draft.get("fav_full_day"))
    for menu_id in menu_ids:
        dish = (draft.get("dishes") or {}).get(menu_id) or {}
        if dish.get("operation") is not None:
            st.session_state[f"review_{menu_id}_operation"] = int(dish["operation"])
        if dish.get("nps") is not None:
            st.session_state[f"review_{menu_id}_nps"] = int(dish["nps"])
        if dish.get("favorited") is not None:
            st.session_state[f"review_{menu_id}_fav_dish"] = bool(dish["favorited"])


def persist_review_draft(day: str, menu_ids: list[str], *, completed: bool = False) -> None:
    payload = collect_review_draft_from_session(menu_ids)
    payload["completed"] = completed
    save_review_draft(day, payload)


def on_morning_change(today_iso: str) -> None:
    autosave_morning_context(today_iso)


def on_review_field_change(day: str, menu_ids: list[str]) -> None:
    if review_day_submitted(day):
        return
    persist_review_draft(day, menu_ids)
