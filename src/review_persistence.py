"""Persist and restore morning + evening review state."""

from __future__ import annotations

import streamlit as st

from src.database import get_logs_for_date, load_review_draft, save_morning_context, save_review_draft

_MORNING_SIG_KEY = "eb_morning_disk_sig"
_MORNING_KEYS = ("morning_sleep", "morning_load", "morning_meal_count")


def mark_morning_disk_signature(today_iso: str, sleep: str, load: str, meal_count: int) -> None:
    st.session_state[_MORNING_SIG_KEY] = f"{today_iso}|{sleep}|{load}|{meal_count}"


def morning_section_complete() -> bool:
    return all(st.session_state.get(key) is not None for key in _MORNING_KEYS)


def dish_section_complete(menu_ids: list[str]) -> bool:
    if not menu_ids:
        return False
    for menu_id in menu_ids:
        if st.session_state.get(f"review_{menu_id}_operation") is None:
            return False
        if st.session_state.get(f"review_{menu_id}_nps") is None:
            return False
    return True


def day_section_complete() -> bool:
    return (
        st.session_state.get("review_day_mood") is not None
        and st.session_state.get("review_day_energy") is not None
    )


def autosave_morning_context(today_iso: str) -> None:
    """Write morning three questions to DB when all three are answered."""
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


def try_save_morning_section(today_iso: str) -> bool:
    """Persist morning block only after all three questions are picked."""
    if not morning_section_complete():
        return False
    autosave_morning_context(today_iso)
    return True


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
    """Fill missing review picks from DB without overwriting in-progress session."""
    if review_day_submitted(day):
        return
    draft = load_review_draft(day)
    if not draft:
        return
    if st.session_state.get("review_day_mood") is None and draft.get("day_mood") is not None:
        st.session_state.review_day_mood = int(draft["day_mood"])
    if st.session_state.get("review_day_energy") is None and draft.get("day_energy") is not None:
        st.session_state.review_day_energy = int(draft["day_energy"])
    if "review_fav_full_day" not in st.session_state and "fav_full_day" in draft:
        st.session_state.review_fav_full_day = bool(draft.get("fav_full_day"))
    for menu_id in menu_ids:
        dish = (draft.get("dishes") or {}).get(menu_id) or {}
        op_key = f"review_{menu_id}_operation"
        nps_key = f"review_{menu_id}_nps"
        fav_key = f"review_{menu_id}_fav_dish"
        if st.session_state.get(op_key) is None and dish.get("operation") is not None:
            st.session_state[op_key] = int(dish["operation"])
        if st.session_state.get(nps_key) is None and dish.get("nps") is not None:
            st.session_state[nps_key] = int(dish["nps"])
        if st.session_state.get(fav_key) is None and dish.get("favorited") is not None:
            st.session_state[fav_key] = bool(dish["favorited"])


def _merge_review_drafts(existing: dict, fresh: dict, menu_ids: list[str]) -> dict:
    dishes: dict[str, dict] = dict(existing.get("dishes") or {})
    for menu_id in menu_ids:
        prev = dict(dishes.get(menu_id) or {})
        incoming = (fresh.get("dishes") or {}).get(menu_id) or {}
        merged = {**prev, **incoming}
        if merged:
            dishes[menu_id] = merged
    day_mood = fresh.get("day_mood")
    if day_mood is None:
        day_mood = existing.get("day_mood")
    day_energy = fresh.get("day_energy")
    if day_energy is None:
        day_energy = existing.get("day_energy")
    fav_full_day = fresh.get("fav_full_day")
    if fav_full_day is None and "fav_full_day" in existing:
        fav_full_day = existing.get("fav_full_day")
    return {
        "day_mood": day_mood,
        "day_energy": day_energy,
        "fav_full_day": bool(fav_full_day) if fav_full_day is not None else False,
        "dishes": dishes,
        "completed": False,
    }


def persist_review_draft(day: str, menu_ids: list[str], *, completed: bool = False) -> None:
    existing = load_review_draft(day) or {}
    fresh = collect_review_draft_from_session(menu_ids)
    payload = _merge_review_drafts(existing, fresh, menu_ids)
    payload["completed"] = completed
    save_review_draft(day, payload)


def try_persist_dish_section(day: str, menu_ids: list[str]) -> bool:
    if review_day_submitted(day) or not dish_section_complete(menu_ids):
        return False
    persist_review_draft(day, menu_ids)
    return True


def try_persist_day_section(day: str, menu_ids: list[str]) -> bool:
    if review_day_submitted(day) or not day_section_complete():
        return False
    persist_review_draft(day, menu_ids)
    return True


def on_morning_change(today_iso: str) -> None:
    try_save_morning_section(today_iso)


def on_review_field_change(day: str, menu_ids: list[str]) -> None:
    try_persist_day_section(day, menu_ids)
