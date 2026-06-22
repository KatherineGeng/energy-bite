"""Load persisted daily state into Streamlit session."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.database import load_daily_meal_plan, load_morning_context
from src.meal_plan_utils import empty_meal_plan


def hydrate_today_state() -> None:
    today = date.today().isoformat()
    st.session_state.today_date = today

    if st.session_state.get("_hydrated_date") == today:
        return

    saved_plan = load_daily_meal_plan(today)
    if saved_plan:
        plan = saved_plan["plan"]
        st.session_state.meal_plan = plan
        st.session_state.current_day_menus = saved_plan["menu_ids"]
        st.session_state.today_recommendations = saved_plan["menu_ids"]
        if saved_plan["confirmed"]:
            st.session_state.menu_locked = True
            st.session_state.final_meal_plan = {k: list(v) for k, v in plan.items()}
            st.session_state.final_daily_list = list(saved_plan["menu_ids"])
        else:
            st.session_state.menu_locked = False
            st.session_state.final_meal_plan = empty_meal_plan()
            st.session_state.final_daily_list = []

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

    st.session_state._hydrated_date = today


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
            return {"date": target, "plan": plan, "menu_ids": menu_ids, "confirmed": True}
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
