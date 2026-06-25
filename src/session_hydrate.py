"""Load persisted daily state into Streamlit session."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.client_profile import plan_user_key
from src.database import load_daily_meal_plan, load_morning_context, save_daily_meal_plan
from src.meal_plan_utils import empty_meal_plan, flatten_plan
from src.plan_bootstrap import plan_from_query_token
from src.query_nav import clear_query_key, qp_first


def sync_session_date() -> str:
    """Always align session to the real calendar day (fixes stale date after midnight)."""
    today = date.today().isoformat()
    prev = st.session_state.get("today_date")
    st.session_state.today_date = today
    if prev and prev != today:
        st.session_state.pop("_hydrated_date", None)
        st.session_state.pop("_hydrated_user", None)
        st.session_state.pop("morning_context_loaded", None)
        st.session_state.pop("eb_fav_auto_date", None)
        if st.session_state.get("menu_gen_date") != today:
            st.session_state.menu_gen_date = today
            st.session_state.menu_gen_count = 0
        st.session_state.meal_plan = empty_meal_plan()
        st.session_state.current_day_menus = []
        st.session_state.today_recommendations = []
        st.session_state.today_menus = []
        st.session_state.menu_locked = False
        st.session_state.final_meal_plan = empty_meal_plan()
        st.session_state.final_daily_list = []
        st.session_state.eb_plan_snapshots = {}
        st.session_state.eb_add_ui = None
    return today


def clear_hydration_markers() -> None:
    """Reset daily hydrate flags (logout / profile switch)."""
    for key in (
        "_hydrated_date",
        "_hydrated_user",
        "morning_context_loaded",
        "morning_sleep",
        "morning_load",
        "morning_meal_count",
        "morning_inputs",
    ):
        st.session_state.pop(key, None)


def apply_morning_context_from_disk(day: str | None = None) -> bool:
    """Load saved morning answers into session — never overwrite in-progress picks."""
    from src.review_persistence import mark_morning_disk_signature, morning_section_complete

    target = day or st.session_state.get("today_date", date.today().isoformat())
    ctx = load_morning_context(target)
    if not ctx:
        return False
    if st.session_state.get("morning_sleep") is None:
        st.session_state.morning_sleep = ctx["sleep"]
    if st.session_state.get("morning_load") is None:
        st.session_state.morning_load = ctx["load"]
    if st.session_state.get("morning_meal_count") is None:
        st.session_state.morning_meal_count = int(ctx["meal_count"])
    if morning_section_complete():
        st.session_state.morning_inputs = {
            "sleep": str(st.session_state.morning_sleep),
            "load": str(st.session_state.morning_load),
            "meal_count": int(st.session_state.morning_meal_count),
        }
        st.session_state.morning_context_loaded = target
        mark_morning_disk_signature(
            target,
            str(st.session_state.morning_sleep),
            str(st.session_state.morning_load),
            int(st.session_state.morning_meal_count),
        )
    return True


def clear_menu_session_state() -> None:
    """Reset menu-related session when user profile is not ready."""
    st.session_state.meal_plan = empty_meal_plan()
    st.session_state.current_day_menus = []
    st.session_state.today_recommendations = []
    st.session_state.today_menus = []
    st.session_state.final_meal_plan = empty_meal_plan()
    st.session_state.final_daily_list = []
    st.session_state.menu_locked = False
    st.session_state.eb_add_ui = None
    st.session_state.eb_plan_snapshots = {}
    clear_hydration_markers()


def _apply_saved_plan(saved: dict) -> None:
    plan = saved["plan"]
    st.session_state.meal_plan = plan
    st.session_state.current_day_menus = saved["menu_ids"]
    st.session_state.today_recommendations = saved["menu_ids"]
    st.session_state.eb_plan_snapshots = saved.get("snapshots", {})
    if saved["confirmed"]:
        st.session_state.menu_locked = True
        st.session_state.final_meal_plan = {k: list(v) for k, v in plan.items()}
        st.session_state.final_daily_list = list(saved["menu_ids"])
    else:
        st.session_state.menu_locked = False
        st.session_state.final_meal_plan = empty_meal_plan()
        st.session_state.final_daily_list = []


def ensure_today_plan_persisted() -> None:
    """Write session menu to CSV when disk is missing (heals reboot / legacy rows)."""
    from src.client_profile import plan_user_key

    if not plan_user_key():
        return

    today = st.session_state.get("today_date", date.today().isoformat())
    if load_daily_meal_plan(today):
        return

    locked = bool(st.session_state.get("menu_locked"))
    plan = st.session_state.get("final_meal_plan") if locked else st.session_state.get("meal_plan")
    if not plan or not isinstance(plan, dict):
        return
    menu_ids = flatten_plan(plan)
    if not menu_ids:
        return

    save_daily_meal_plan(today, plan, confirmed=locked)
    from src.database import record_menu_archive

    record_menu_archive(today, menu_ids)
    from src.db_config import postgres_enabled

    if not postgres_enabled():
        from src.plan_bootstrap import persist_plan_to_browser

        persist_plan_to_browser(
            today,
            plan,
            confirmed=locked,
            snapshots=st.session_state.get("eb_plan_snapshots", {}),
        )


def hydrate_today_state() -> None:
    today = date.today().isoformat()
    user_key = plan_user_key()
    st.session_state.today_date = today

    if not user_key:
        return

    if (
        st.session_state.get("_hydrated_date") == today
        and st.session_state.get("_hydrated_user") == user_key
    ):
        ensure_today_plan_persisted()
        apply_morning_context_from_disk(today)
        return

    saved_plan = load_daily_meal_plan(today)
    if not saved_plan:
        from src.db_config import postgres_enabled

        if not postgres_enabled():
            token_plan = plan_from_query_token()
            if token_plan and token_plan.get("date") == today:
                saved_plan = token_plan
                if qp_first("ebplan"):
                    clear_query_key("ebplan")

    if saved_plan:
        _apply_saved_plan(saved_plan)
    else:
        st.session_state.meal_plan = empty_meal_plan()
        st.session_state.current_day_menus = []
        st.session_state.today_recommendations = []
        st.session_state.menu_locked = False
        st.session_state.final_meal_plan = empty_meal_plan()
        st.session_state.final_daily_list = []
        st.session_state.eb_plan_snapshots = {}

    ctx = load_morning_context(today)
    if ctx:
        st.session_state.morning_sleep = ctx["sleep"]
        st.session_state.morning_load = ctx["load"]
        st.session_state.morning_meal_count = int(ctx["meal_count"])
        st.session_state.morning_inputs = {
            "sleep": ctx["sleep"],
            "load": ctx["load"],
            "meal_count": int(ctx["meal_count"]),
        }
        st.session_state.morning_context_loaded = today
        from src.review_persistence import mark_morning_disk_signature

        mark_morning_disk_signature(today, ctx["sleep"], ctx["load"], int(ctx["meal_count"]))
    elif st.session_state.get("morning_context_loaded") != today:
        in_progress = any(st.session_state.get(key) is not None for key in ("morning_sleep", "morning_load", "morning_meal_count"))
        if not in_progress:
            for key in ("morning_sleep", "morning_load", "morning_meal_count", "morning_inputs"):
                st.session_state.pop(key, None)

    st.session_state._hydrated_date = today
    st.session_state._hydrated_user = user_key
    ensure_today_plan_persisted()


def get_confirmed_plan(day: str | None = None) -> dict | None:
    """Return confirmed plan for a date (disk first, then session for today)."""
    target = day or st.session_state.get("today_date", date.today().isoformat())
    saved = load_daily_meal_plan(target)
    if saved and saved["confirmed"] and saved["menu_ids"]:
        return saved

    if target == st.session_state.get("today_date") and st.session_state.get("menu_locked"):
        menu_ids = list(st.session_state.get("final_daily_list") or [])
        if menu_ids:
            plan = st.session_state.get("final_meal_plan") or {}
            return {
                "date": target,
                "plan": plan,
                "menu_ids": menu_ids,
                "confirmed": True,
                "snapshots": st.session_state.get("eb_plan_snapshots", {}),
            }
    return None


def menu_ids_for_date(day: str) -> list[str]:
    saved = load_daily_meal_plan(day)
    if saved and saved["menu_ids"]:
        return list(saved["menu_ids"])
    if day == st.session_state.get("today_date", date.today().isoformat()):
        if st.session_state.get("menu_locked"):
            return list(st.session_state.get("final_daily_list") or [])
        return list(st.session_state.get("current_day_menus") or [])
    return []
