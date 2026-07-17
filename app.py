"""
简愈一人食 — V4.0
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.app_time import beijing_today
from src.constants import APP_VERSION
from src.database import init_database
from src.mobile_ui import inject_mobile_css, render_bottom_nav, render_top_header
from src.pwa_head import inject_pwa_head
from src.query_nav import apply_query_nav
from src.session_hydrate import clear_menu_session_state, hydrate_today_state, sync_session_date
from src.review_nav_state import is_review_chip_navigation, restore_review_picks_from_query
from src.session_hydrate import is_secondary_page_navigation
from src.profile_bootstrap import restore_profile_from_browser
from src.query_nav import qp_first
from src.theme import inject_theme_assets
from src.user_profile import profile_complete, render_onboarding

# 鼠尾草绿底色，白色粗体「简」字的极简 SVG 图标（Data URI，零外链加载）
icon_svg = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' fill='%238DA399'/>"
    "<text x='50' y='50' font-family='sans-serif' font-size='60' font-weight='bold' "
    "fill='white' text-anchor='middle' dominant-baseline='central'>%E7%AE%80</text>"
    "</svg>"
)
st.set_page_config(
    page_title="简愈一人食",
    page_icon=icon_svg,
    layout="centered",
    initial_sidebar_state="collapsed",
)

import streamlit.components.v1 as components

# 强行注入 iOS PWA 标签与清空默认图标（parent document，绕过 Streamlit SPA 延迟）
components.html(
    """
    <script>
    const parent = window.parent.document;

    // 1. 强制覆盖网页真实标题
    parent.title = "简愈一人食";

    // 2. 强制写入 iOS 桌面应用名称
    let titleMeta = parent.querySelector('meta[name="apple-mobile-web-app-title"]');
    if (!titleMeta) {
        titleMeta = parent.createElement('meta');
        titleMeta.name = "apple-mobile-web-app-title";
        parent.head.appendChild(titleMeta);
    }
    titleMeta.content = "简愈一人食";

    // 3. 移除 Streamlit 默认的所有红色图标，逼迫苹果系统重新生成「简」字默认图标
    const icons = parent.querySelectorAll('link[rel="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]');
    icons.forEach(icon => icon.remove());
    </script>
    """,
    height=0,
    width=0,
)

init_database()
inject_pwa_head()
inject_theme_assets()
inject_mobile_css()

sync_session_date()
restore_review_picks_from_query()
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
    st.session_state.menu_gen_date = beijing_today().isoformat()
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
if "poster_cache" not in st.session_state:
    st.session_state.poster_cache = {}
if "poster_b64_cache" not in st.session_state:
    st.session_state.poster_b64_cache = {}

VALID_PAGES = {"morning", "night", "export", "mine", "admin"}
apply_query_nav(VALID_PAGES)

from src.db_config import postgres_enabled

if postgres_enabled():
    from src.db_auth import restore_session_user

    restore_session_user()
else:
    from src.client_profile import sync_profile_from_url

    sync_profile_from_url()
    restore_profile_from_browser()

    from src.user_vault import ensure_vault_synced
    from src.plan_bootstrap import restore_plan_from_browser
    from src.menu_bootstrap import restore_menus_from_browser

    ensure_vault_synced()
    restore_plan_from_browser()
    restore_menus_from_browser()

_page = st.session_state.current_page
_is_admin = _page == "admin" or qp_first("nav") == "admin"

render_top_header(beijing_today())

if not _is_admin and not profile_complete():
    clear_menu_session_state()
    render_onboarding()
    st.stop()

hydrate_today_state(lightweight=is_review_chip_navigation() or is_secondary_page_navigation())

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
