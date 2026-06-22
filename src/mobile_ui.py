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
    st.markdown(
        f"""
        <style>
        *, *::before, *::after {{ box-sizing: border-box !important; }}
        html, body, .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        section.main, .block-container {{
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: clip !important;
        }}
        [data-testid="stToolbar"],
        [data-testid="stToolbarActions"],
        [data-testid="stAppDeployButton"],
        [data-testid="stDecoration"],
        .stAppDeployButton, #MainMenu,
        .viewerBadge_container, div[class*="viewerBadge"],
        button[kind="header"], [data-testid="baseButton-header"],
        [data-testid="stSidebar"], header[data-testid="stHeader"], footer {{
            display: none !important;
        }}
        .block-container {{
            padding: 0.25rem max(0.65rem, env(safe-area-inset-left)) calc(4.6rem + env(safe-area-inset-bottom)) max(0.65rem, env(safe-area-inset-right)) !important;
        }}
        p, span, label, .stMarkdown {{
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
        }}
        .eb-action-row, .eb-bottom-nav {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            justify-content: space-between !important;
            gap: 0.35rem !important;
            width: 100% !important;
            max-width: 100% !important;
        }}
        .eb-bottom-nav {{
            position: fixed !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            z-index: 999999 !important;
            background: rgba(249, 248, 246, 0.98) !important;
            border-top: 1px solid rgba(141, 163, 153, 0.28) !important;
            padding: 0.38rem max(0.65rem, env(safe-area-inset-left)) calc(0.42rem + env(safe-area-inset-bottom)) max(0.65rem, env(safe-area-inset-right)) !important;
            box-shadow: 0 -4px 16px rgba(30, 41, 59, 0.06) !important;
        }}
        [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.35rem !important;
            width: 100% !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            flex: 1 1 0 !important;
            width: auto !important;
            min-width: 0 !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] .stButton > button {{
            font-size: 0.68rem !important;
            padding: 0.38rem 0.15rem !important;
            white-space: nowrap !important;
        }}
        .eb-meal-headline {{
            font-size: 0.82rem;
            line-height: 1.45;
            margin: 0 0 0.2rem;
            color: {TEXT};
        }}
        .eb-meal-label {{
            font-family: inherit;
            font-weight: 600;
        }}
        .eb-meal-meta {{
            color: #64748B;
            font-size: 0.76rem;
        }}
        .eb-add-panel {{
            background: rgba(141, 163, 153, 0.08);
            border: 1px solid rgba(141, 163, 153, 0.25);
            border-radius: 10px;
            padding: 0.55rem 0.65rem;
            margin: 0.35rem 0 0.5rem;
        }}
        .eb-cov-wrap {{
            position: relative;
            display: inline;
            white-space: normal;
        }}
        .eb-cov-i {{
            display: inline-block;
            position: relative;
            margin-left: 0.12rem;
            width: 0.9rem;
            height: 0.9rem;
            line-height: 0.85rem;
            text-align: center;
            font-size: 0.58rem;
            font-weight: 700;
            font-style: italic;
            color: {ACCENT};
            border: 1px solid rgba(141, 163, 153, 0.55);
            border-radius: 50%;
            cursor: help;
            vertical-align: super;
            text-decoration: none;
        }}
        .eb-cov-wrap .eb-cov-tip {{
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}
        .eb-cov-wrap:hover .eb-cov-tip,
        .eb-cov-wrap:focus-within .eb-cov-tip {{
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }}
        .eb-cov-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0.35rem 0;
            font-size: 0.7rem;
        }}
        .eb-cov-table th, .eb-cov-table td {{
            border-bottom: 1px solid rgba(141, 163, 153, 0.2);
            padding: 0.2rem 0.15rem;
        }}
        .eb-cov-mark {{ text-align: center; color: {ACCENT}; }}
        .eb-cov-foot {{ display: block; color: #64748B; font-size: 0.66rem; margin-top: 0.15rem; }}
        .eb-cov-hint {{ display: block; color: #94A3B8; font-size: 0.6rem; margin-top: 0.2rem; }}
        .eb-action-row {{ margin: 0.35rem 0 0.5rem !important; }}
        .eb-action-row .eb-action-btn {{ max-width: 50% !important; }}
        .eb-action-row .eb-action-btn:only-child {{ max-width: 100% !important; flex: 1 1 100% !important; }}
        .eb-bottom-nav .eb-nav-link {{ max-width: 33.33% !important; }}
        .eb-action-btn, .eb-nav-link {{
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
        .eb-action-btn.disabled, .eb-action-btn.disabled:hover {{
            opacity: 0.45 !important;
            pointer-events: none !important;
        }}
        .eb-action-icon, .eb-nav-icon {{
            display: inline-block !important;
            font-size: 0.85rem !important;
            line-height: 1 !important;
            margin: 0 !important;
            flex-shrink: 0 !important;
        }}
        .eb-nav-link.active {{
            background: rgba(141, 163, 153, 0.2) !important;
            color: {ACCENT} !important;
            border-color: rgba(141, 163, 153, 0.45) !important;
            font-weight: 600 !important;
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
        .eb-meal-section {{
            margin-bottom: 0.65rem;
        }}
        .eb-meal-section-title {{
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 600;
            color: {TEXT};
            margin: 0 0 0.35rem;
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


def render_bottom_nav(current_page: str | None = None) -> None:
    page = current_page or st.session_state.get("current_page", "morning")
    parts: list[str] = []
    for page_id, icon, label in NAV_ITEMS:
        active = " active" if page_id == page else ""
        parts.append(
            f'<a class="eb-nav-link{active}" href="?nav={page_id}">'
            f'<span class="eb-nav-icon">{icon}</span><span>{label}</span></a>'
        )
    st.markdown(f'<div class="eb-bottom-nav">{"".join(parts)}</div>', unsafe_allow_html=True)
