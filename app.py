"""
简愈一人食 — V4.0
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.constants import APP_VERSION
from src.database import init_database
from src.mobile_ui import inject_mobile_css, render_bottom_nav, render_top_header
from src.pwa_head import inject_pwa_head
from src.query_nav import apply_query_nav
from src.session_hydrate import clear_menu_session_state, hydrate_today_state, sync_session_date
from src.client_profile import sync_profile_from_url
from src.profile_bootstrap import restore_profile_from_browser
from src.query_nav import qp_first
from src.theme import inject_theme_assets
from src.user_profile import profile_complete, render_onboarding

st.set_page_config(
    page_title=f"简愈一人食 {APP_VERSION}",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

init_database()
inject_pwa_head()
inject_theme_assets()
inject_mobile_css()

sync_session_date()
if "morning_inputs" not in st.session_state:
    st.session_state.morning_inputs = {}
if "today_recommendations" not in st.session_state:
    st.session_state.today_recommendations = []
if "today_menus" not in st.session_state:
    st.session_state.today_menus = []
if "current_day_menus" not in st.session_state:
    st.session_state.current_day_menus = []
if "meal_plan" not in st.session_state:
    st.session_state.meal_plan = {"早餐": [], "午餐": [], "晚餐": []}
if "final_meal_plan" not in st.session_state:
    st.session_state.final_meal_plan = {"早餐": [], "午餐": [], "晚餐": []}
if "final_daily_list" not in st.session_state:
    st.session_state.final_daily_list = []
if "menu_locked" not in st.session_state:
    st.session_state.menu_locked = False
if "last_log_id" not in st.session_state:
    st.session_state.last_log_id = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "morning"
if "show_share_guide" not in st.session_state:
    st.session_state.show_share_guide = False
if "review_complete" not in st.session_state:
    st.session_state.review_complete = False
if "eb_add_ui" not in st.session_state:
    st.session_state.eb_add_ui = None
if "menu_gen_count" not in st.session_state:
    st.session_state.menu_gen_count = 0
if "menu_gen_date" not in st.session_state:
    st.session_state.menu_gen_date = date.today().isoformat()
if "last_gen_source" not in st.session_state:
    st.session_state.last_gen_source = None
if "last_gen_note" not in st.session_state:
    st.session_state.last_gen_note = None
if "ai_fresh_menu_ids" not in st.session_state:
    st.session_state.ai_fresh_menu_ids = []
if "export_action_panel" not in st.session_state:
    st.session_state.export_action_panel = None

if "poster_history" not in st.session_state:
    st.session_state.poster_history = []

VALID_PAGES = {"morning", "night", "export", "mine", "admin"}
apply_query_nav(VALID_PAGES)
restore_profile_from_browser()
sync_profile_from_url()

from src.user_vault import ensure_vault_synced
from src.plan_bootstrap import restore_plan_from_browser
from src.menu_bootstrap import restore_menus_from_browser

ensure_vault_synced()
restore_plan_from_browser()
restore_menus_from_browser()

_page = st.session_state.current_page
_is_admin = _page == "admin" or qp_first("nav") == "admin"

render_top_header(date.today())

if not _is_admin and not profile_complete():
    clear_menu_session_state()
    render_onboarding()
    st.stop()

hydrate_today_state()

if _page == "morning":
    from pages import morning

    morning.render()
elif _page == "night":
    from pages import night_checkin

    night_checkin.render()
elif _page == "admin":
    from pages import admin

    admin.render()
elif _page == "mine":
    from pages import mine

    mine.render()
else:
    from pages import export_poster

    export_poster.render()

if _page != "admin" and not _is_admin:
    render_bottom_nav()
