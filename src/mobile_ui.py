"""Mobile-first layout helpers for 简愈一人食."""

from __future__ import annotations

from datetime import date

import streamlit as st

from urllib.parse import quote

from src.calendar_utils import display_version, format_today_cn
from src.constants import APP_VERSION
from src.nav_params import append_nav_params
from src.theme import ACCENT, TEXT
from src.user_profile import nickname

NAV_ITEMS = [
    ("morning", "☀️", "菜单"),
    ("night", "🍃", "回顾"),
    ("export", "📤", "分享"),
]

MENU_GEN_ICON = (
    '<svg class="eb-menu-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<circle cx="12" cy="13.5" r="6.25"/>'
    '<path d="M7.25 2.75v6.25c0 .97-.78 1.75-1.75 1.75S3.75 9.97 3.75 9V2.75"/>'
    '<path d="M5.5 2.75v4"/>'
    '<path d="M18.25 2.75V10l-2 2.75"/>'
    '<path d="M16.25 2.75h4"/>'
    "</svg>"
)


def inject_mobile_css() -> None:
    """Safari-safe CSS — no backdrop-filter, no global Streamlit layout overrides."""
    st.markdown(
        f"""
        <style>
        header[data-testid="stHeader"] {{
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            visibility: hidden !important;
        }}
        .stApp {{
            padding-top: env(safe-area-inset-top, 0px) !important;
        }}
        .block-container {{
            padding: max(1.1rem, env(safe-area-inset-top, 0px) + 0.5rem) max(0.65rem, env(safe-area-inset-left)) calc(3.6rem + env(safe-area-inset-bottom)) max(0.65rem, env(safe-area-inset-right)) !important;
        }}
        [data-testid="stToolbar"],
        [data-testid="stToolbarActions"],
        [data-testid="stAppDeployButton"],
        [data-testid="stDecoration"],
        .stAppDeployButton, #MainMenu,
        .viewerBadge_container, div[class*="viewerBadge"],
        button[kind="header"], [data-testid="baseButton-header"],
        [data-testid="stSidebar"], footer {{
            display: none !important;
        }}
        p, span, label, .stMarkdown {{
            overflow-wrap: break-word !important;
            word-break: keep-all !important;
        }}
        .eb-action-row {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            justify-content: space-between !important;
            gap: 0.35rem !important;
            width: 100% !important;
            margin: 0.35rem 0 0.5rem !important;
        }}
        .eb-action-row .eb-action-btn {{ max-width: 50% !important; }}
        .eb-action-row .eb-action-btn:only-child {{ max-width: 100% !important; flex: 1 1 100% !important; }}
        /* 固定底栏 — 纯色背景，Safari 不用 backdrop-filter */
        .eb-bottom-nav {{
            position: fixed !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            z-index: 999 !important;
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            justify-content: space-around !important;
            width: 100% !important;
            height: calc(3.15rem + env(safe-area-inset-bottom)) !important;
            padding: 0 0 env(safe-area-inset-bottom) 0 !important;
            margin: 0 !important;
            background: #ffffff !important;
            border-top: 1px solid rgba(30, 41, 59, 0.1) !important;
            box-shadow: 0 -1px 8px rgba(30, 41, 59, 0.06) !important;
        }}
        .eb-bottom-nav .eb-nav-link {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            max-width: 33.33% !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.12rem !important;
            text-decoration: none !important;
            padding: 0.28rem 0 !important;
            font-size: 0.78rem !important;
            line-height: 1.1 !important;
            color: #64748B !important;
            background: transparent !important;
            -webkit-tap-highlight-color: transparent;
        }}
        .eb-nav-link.active {{
            color: {ACCENT} !important;
            font-weight: 600 !important;
        }}
        .eb-nav-icon {{
            font-size: 1.35rem !important;
            line-height: 1 !important;
        }}
        .eb-action-icon {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex-shrink: 0 !important;
        }}
        .eb-menu-svg {{
            width: 1.35rem !important;
            height: 1.35rem !important;
            display: block !important;
        }}
        .eb-gen-btn {{
            display: block !important;
            width: auto !important;
            min-width: 11rem !important;
            max-width: 18rem !important;
            margin: 0.65rem auto !important;
            padding: 0.72rem 1.5rem !important;
            font-size: 1.05rem !important;
            text-align: center !important;
            box-sizing: border-box !important;
        }}
        .eb-meal-action-row {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            justify-content: space-between !important;
            gap: 0.35rem !important;
            width: 100% !important;
            margin: 0.35rem 0 0.15rem !important;
        }}
        .eb-meal-action-btn {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-decoration: none !important;
            border-radius: 8px !important;
            padding: 0.55rem 0.2rem !important;
            font-size: 0.88rem !important;
            line-height: 1.2 !important;
            color: {TEXT} !important;
            background: rgba(255,255,255,0.9) !important;
            border: 1px solid rgba(141, 163, 153, 0.32) !important;
            -webkit-tap-highlight-color: transparent;
            white-space: nowrap !important;
        }}
        .eb-meal-action-btn.primary {{
            background: {ACCENT} !important;
            color: #fff !important;
            border-color: {ACCENT} !important;
            font-weight: 600 !important;
        }}
        [data-testid="stColumn"] .stPopover > button {{
            width: auto !important;
            min-height: unset !important;
            height: auto !important;
            padding: 0 !important;
            margin: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {ACCENT} !important;
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            justify-content: flex-start !important;
        }}
        [data-testid="stColumn"] .stPopover {{
            margin-top: -0.15rem !important;
        }}
        .eb-action-btn {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.28rem !important;
            text-decoration: none !important;
            border-radius: 10px !important;
            padding: 0.55rem 0.25rem !important;
            font-size: 1.05rem !important;
            line-height: 1.2 !important;
            color: {TEXT} !important;
            background: rgba(255,255,255,0.85) !important;
            border: 1px solid rgba(141, 163, 153, 0.28) !important;
            -webkit-tap-highlight-color: transparent;
        }}
        .eb-action-btn.primary {{
            background: {ACCENT} !important;
            color: #fff !important;
            border-color: {ACCENT} !important;
            font-weight: 600 !important;
        }}
        .eb-action-btn.disabled {{
            opacity: 0.45 !important;
            pointer-events: none !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.35rem !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {{
            font-size: 0.68rem !important;
            padding: 0.38rem 0.15rem !important;
        }}
        .eb-app-header {{
            text-align: center;
            margin: 0 0 0.45rem;
            padding-top: 0.15rem;
        }}
        .eb-title-version {{
            display: block;
            font-size: 0.85rem;
            color: {ACCENT};
            font-weight: 700;
            text-align: center;
            margin: 0 0 0.2rem;
            line-height: 1.2;
        }}
        .eb-app-title {{
            text-align: center;
            color: {TEXT};
            margin: 0 0 0.15rem;
            font-size: 1.85rem;
            font-weight: 600;
            line-height: 1.35;
            white-space: nowrap;
            font-family: "PingFang SC", "Noto Serif SC", "Songti SC", serif;
        }}
        .eb-meal-meta-inline {{
            font-size: 0.95rem;
            color: #64748B;
            line-height: 1.45;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child .stPopover {{
            margin-top: 0 !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child {{
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child .stPopover > button {{
            width: auto !important;
            min-height: unset !important;
            height: auto !important;
            padding: 0.05rem 0.35rem !important;
            margin: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: {ACCENT} !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            white-space: nowrap !important;
        }}
        .eb-date-line {{
            text-align: center;
            font-size: 1rem;
            color: {ACCENT};
            font-weight: 700;
            margin: 0;
            line-height: 1.35;
        }}
        div[data-testid="stRadio"] > div {{ flex-wrap: wrap !important; gap: 0.35rem !important; }}
        div[data-testid="stRadio"] label {{
            font-size: 1.05rem !important;
            padding: 0.35rem 0.55rem !important;
        }}
        /* 日历 — 有菜单深色可点，无菜单灰色 */
        .eb-cal {{ margin: 0.5rem 0 0.75rem; user-select: none; }}
        .eb-cal-head {{
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 0.55rem;
        }}
        .eb-cal-title {{ font-size: 1.15rem; font-weight: 600; color: {TEXT}; }}
        .eb-cal-nav {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 2.4rem; height: 2.4rem; border-radius: 10px;
            border: 1px solid rgba(141,163,153,0.4); background: #fff;
            color: {ACCENT}; text-decoration: none; font-size: 1.2rem;
        }}
        .eb-cal-weekdays, .eb-cal-grid {{
            display: grid; grid-template-columns: repeat(7, 1fr);
            gap: 0.25rem; text-align: center;
        }}
        .eb-cal-weekdays span {{
            font-size: 0.95rem; color: #94A3B8; padding: 0.2rem 0;
        }}
        .eb-cal-day {{
            display: flex; align-items: center; justify-content: center;
            aspect-ratio: 1; border-radius: 10px; font-size: 1.05rem;
            text-decoration: none; border: 1px solid transparent;
        }}
        .eb-cal-day.active {{
            color: {TEXT}; font-weight: 700; background: #fff;
            border-color: rgba(141,163,153,0.35);
        }}
        .eb-cal-day.active.selected {{
            background: rgba(141,163,153,0.22);
            border-color: {ACCENT};
        }}
        .eb-cal-day.disabled {{
            color: #CBD5E1; pointer-events: none; cursor: default;
        }}
        .eb-cal-day.empty {{ visibility: hidden; }}
        .eb-cal-day.today:not(.selected) {{ border-color: rgba(141,163,153,0.25); }}
        .eb-cal-hint {{
            font-size: 0.95rem; color: #64748B; text-align: center;
            margin: 0.45rem 0 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_header(for_date: date | None = None) -> None:
    d = for_date or date.today()
    version = display_version(APP_VERSION)
    today_line = format_today_cn(d)
    name = nickname()
    title = f"🌿 {name}的简愈一人食" if name else "🌿 简愈一人食"

    st.markdown(
        f'<div class="eb-app-header">'
        f'<p class="eb-app-title">{title}</p>'
        f'<p class="eb-title-version">{version}</p>'
        f'<p class="eb-date-line">{today_line}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _action_href(act: str) -> str:
    page = st.session_state.get("current_page", "morning")
    return append_nav_params(f"?nav={quote(page)}&act={quote(act)}")


def render_action_row(
    items: list[tuple[str, str, str, bool, bool]],
) -> None:
    """Render horizontal action links: (act_key, icon, label, primary, disabled)."""
    parts: list[str] = []
    for act, icon, label, primary, disabled in items:
        cls = "eb-action-btn"
        if primary:
            cls += " primary"
        if disabled:
            cls += " disabled"
        inner = f'<span class="eb-action-icon">{icon}</span><span>{label}</span>'
        if disabled:
            parts.append(f'<span class="{cls}">{inner}</span>')
        else:
            parts.append(f'<a class="{cls}" href="{_action_href(act)}">{inner}</a>')
    st.markdown(f'<div class="eb-action-row">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_primary_action_link(
    act: str,
    icon: str,
    label: str,
    *,
    disabled: bool = False,
) -> None:
    """Centered primary action via ?act= (mobile-safe)."""
    inner = f'<span class="eb-action-icon">{icon}</span><span>{label}</span>'
    cls = "eb-action-btn primary eb-gen-btn"
    if disabled:
        st.markdown(f'<div style="text-align:center"><span class="{cls} disabled">{inner}</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:center"><a class="{cls}" href="{_action_href(act)}">{inner}</a></div>', unsafe_allow_html=True)


def _meal_action_href(meal_act: str, meal_type: str, menu_id: str | None = None) -> str:
    page = st.session_state.get("current_page", "morning")
    href = f"?nav={quote(page)}&meal_act={quote(meal_act)}&meal={quote(meal_type)}"
    if menu_id:
        href += f"&mid={quote(menu_id)}"
    return append_nav_params(href)


def render_meal_action_row(
    meal_type: str,
    items: list[tuple[str, str, str | None]],
) -> None:
    """Horizontal meal edit links: (act_key, label, menu_id or None)."""
    parts: list[str] = []
    for act, label, menu_id in items:
        href = _meal_action_href(act, meal_type, menu_id)
        parts.append(f'<a class="eb-meal-action-btn" href="{href}">{label}</a>')
    st.markdown(f'<div class="eb-meal-action-row">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_bottom_nav(current_page: str | None = None) -> None:
    """Fixed tab bar at viewport bottom (HTML links, Safari-safe)."""
    page = current_page or st.session_state.get("current_page", "morning")
    parts: list[str] = []
    for page_id, icon, label in NAV_ITEMS:
        active = " active" if page_id == page else ""
        parts.append(
            f'<a class="eb-nav-link{active}" href="{append_nav_params(f"?nav={page_id}")}">'
            f'<span class="eb-nav-icon">{icon}</span>'
            f'<span class="eb-nav-label">{label}</span></a>'
        )
    st.markdown(f'<nav class="eb-bottom-nav">{"".join(parts)}</nav>', unsafe_allow_html=True)
