"""Mobile-first layout helpers for 简愈一人食."""

from __future__ import annotations

import streamlit as st

from src.constants import APP_VERSION
from src.theme import ACCENT, TEXT

NAV_ITEMS = [
    ("morning", "☀️", "晨间"),
    ("night", "🍃", "晚间"),
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
        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"],
        [data-testid="stBottomBlockContainer"],
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
        /* HTML 横排按钮组（不依赖 st.columns） */
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
        .eb-action-row {{ margin: 0.35rem 0 0.5rem !important; }}
        .eb-action-row .eb-action-btn {{ max-width: 50% !important; }}
        .eb-bottom-nav .eb-nav-link {{ max-width: 33.33% !important; }}
        .eb-action-btn, .eb-nav-link {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            text-align: center !important;
            text-decoration: none !important;
            border-radius: 10px !important;
            padding: 0.42rem 0.15rem !important;
            font-size: 0.72rem !important;
            line-height: 1.25 !important;
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
            display: block !important;
            font-size: 1rem !important;
            line-height: 1.1 !important;
            margin-bottom: 0.1rem !important;
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
        .eb-nav-link.active {{
            background: rgba(141, 163, 153, 0.2) !important;
            color: {ACCENT} !important;
            border-color: rgba(141, 163, 153, 0.45) !important;
            font-weight: 600 !important;
        }}
        .eb-version-badge {{
            text-align: center;
            font-size: 0.72rem;
            color: {ACCENT};
            font-weight: 700;
            margin: -0.35rem 0 0.35rem;
        }}
        div[data-testid="stRadio"] > div {{ flex-wrap: wrap !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_header(today: str, favorited_count: int) -> None:
    st.markdown(
        "<h2 style='text-align:center;color:#1E293B;margin:0 0 0.2rem;font-size:1.3rem;'>"
        "<i class='fa-solid fa-leaf' style='color:#8DA399;'></i> 简愈一人食</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="eb-version-badge">版本 {APP_VERSION} · 布局:HTML横排 · 图标:GitHub PNG</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;font-size:0.78rem;color:#64748B;margin:0 0 0.45rem;'>"
        f"今日 {today} · 收藏 {favorited_count} 道</p>",
        unsafe_allow_html=True,
    )


def render_action_row(
    items: list[tuple[str, str, str, bool, bool]],
) -> None:
    """Render compact horizontal action links: (act_key, icon, label, primary, disabled)."""
    parts: list[str] = []
    for act, icon, label, primary, disabled in items:
        cls = "eb-action-btn"
        if primary:
            cls += " primary"
        if disabled:
            cls += " disabled"
        inner = f'<span class="eb-action-icon">{icon}</span>{label}'
        if disabled:
            parts.append(f'<span class="{cls}">{inner}</span>')
        else:
            parts.append(f'<a class="{cls}" href="?act={act}">{inner}</a>')
    st.markdown(f'<div class="eb-action-row">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_bottom_nav(current_page: str | None = None) -> None:
    page = current_page or st.session_state.get("current_page", "morning")
    links: list[str] = []
    for page_id, icon, label in NAV_ITEMS:
        active = " active" if page_id == page else ""
        links.append(
            f'<a class="eb-nav-link{active}" href="?nav={page_id}">'
            f'<span class="eb-nav-icon">{icon}</span>{label}</a>'
        )
    st.markdown(f'<nav class="eb-bottom-nav">{"".join(links)}</nav>', unsafe_allow_html=True)
