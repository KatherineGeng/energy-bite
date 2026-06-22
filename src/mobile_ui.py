"""Mobile-first layout helpers for 简愈一人食."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.calendar_utils import display_version, format_today_cn
from src.constants import APP_VERSION
from src.theme import ACCENT, TEXT

NAV_ITEMS = [
    ("morning", "☀️", "菜单"),
    ("night", "🍃", "回顾"),
    ("export", "📤", "分享"),
]


def inject_mobile_css() -> None:
    """Safari-safe CSS — no backdrop-filter, no global Streamlit layout overrides."""
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding: 0.25rem max(0.65rem, env(safe-area-inset-left)) calc(3.6rem + env(safe-area-inset-bottom)) max(0.65rem, env(safe-area-inset-right)) !important;
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
            word-break: break-word !important;
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
            font-size: 0.62rem !important;
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
            font-size: 1.2rem !important;
            line-height: 1 !important;
        }}
        .eb-gen-btn {{
            display: flex !important;
            width: 100% !important;
            margin: 0.35rem 0 0.5rem !important;
            box-sizing: border-box !important;
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
            padding: 0.42rem 0.2rem !important;
            font-size: 0.72rem !important;
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
        .eb-title-version {{
            font-size: 0.72rem;
            color: {ACCENT};
            font-weight: 700;
            margin-left: 0.35rem;
        }}
        .eb-date-line {{
            text-align: center;
            font-size: 0.72rem;
            color: {ACCENT};
            font-weight: 700;
            margin: 0.1rem 0 0.45rem;
        }}
        div[data-testid="stRadio"] > div {{ flex-wrap: wrap !important; gap: 0.35rem !important; }}
        div[data-testid="stRadio"] label {{
            font-size: 0.82rem !important;
            padding: 0.2rem 0.45rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_header(for_date: date | None = None) -> None:
    d = for_date or date.today()
    version = display_version(APP_VERSION)
    today_line = format_today_cn(d)

    st.markdown(
        f"<h2 style='text-align:center;color:#1E293B;margin:0 0 0.2rem;font-size:1.3rem;'>"
        f"🌿 简愈一人食"
        f"<span class='eb-title-version'>{version}</span></h2>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<p class="eb-date-line">{today_line}</p>', unsafe_allow_html=True)


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
            parts.append(f'<a class="{cls}" href="?act={act}">{inner}</a>')
    st.markdown(f'<div class="eb-action-row">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_primary_action_link(
    act: str,
    icon: str,
    label: str,
    *,
    disabled: bool = False,
) -> None:
    """Full-width primary action via ?act= (mobile-safe, no WebSocket button)."""
    inner = f'<span class="eb-action-icon">{icon}</span><span>{label}</span>'
    cls = "eb-action-btn primary eb-gen-btn"
    if disabled:
        st.markdown(f'<span class="{cls} disabled">{inner}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<a class="{cls}" href="?act={act}">{inner}</a>', unsafe_allow_html=True)


def render_bottom_nav(current_page: str | None = None) -> None:
    """Fixed tab bar at viewport bottom (HTML links, Safari-safe)."""
    page = current_page or st.session_state.get("current_page", "morning")
    parts: list[str] = []
    for page_id, icon, label in NAV_ITEMS:
        active = " active" if page_id == page else ""
        parts.append(
            f'<a class="eb-nav-link{active}" href="?nav={page_id}">'
            f'<span class="eb-nav-icon">{icon}</span>'
            f'<span class="eb-nav-label">{label}</span></a>'
        )
    st.markdown(f'<nav class="eb-bottom-nav">{"".join(parts)}</nav>', unsafe_allow_html=True)
