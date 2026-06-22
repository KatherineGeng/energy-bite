"""
简愈一人食 — V4.0
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.constants import APP_VERSION
from src.database import count_favorited_menus, init_database
from src.mobile_ui import inject_mobile_css, render_bottom_nav, render_top_header
from src.pwa_head import inject_pwa_head
from src.query_nav import apply_query_nav
from src.theme import inject_theme_assets
from pages import export_poster, morning, night_checkin

st.set_page_config(
    page_title=f"简愈一人食 {APP_VERSION}",
    page_icon="apple-touch-icon.png",
    layout="centered",
    initial_sidebar_state="collapsed",
)

init_database()
inject_pwa_head()
inject_theme_assets()
inject_mobile_css()

if "today_date" not in st.session_state:
    st.session_state.today_date = date.today().isoformat()
if "morning_inputs" not in st.session_state:
    st.session_state.morning_inputs = {}
if "today_recommendations" not in st.session_state:
    st.session_state.today_recommendations = []
if "today_menus" not in st.session_state:
    st.session_state.today_menus = []
if "current_day_menus" not in st.session_state:
    st.session_state.current_day_menus = []
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

PAGE_MAP = {
    "morning": morning.render,
    "night": night_checkin.render,
    "export": export_poster.render,
}

apply_query_nav(set(PAGE_MAP.keys()))

render_top_header(st.session_state.today_date, count_favorited_menus())
PAGE_MAP[st.session_state.current_page]()
render_bottom_nav()
