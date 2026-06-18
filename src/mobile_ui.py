"""Mobile-first layout helpers for Energy Bite."""

from __future__ import annotations

import streamlit as st

from src.theme import ACCENT, TEXT

NAV_ITEMS = [
    ("morning", "晨间餐饮"),
    ("night", "晚间回顾"),
    ("export", "收藏分享"),
]


def inject_mobile_css() -> None:
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
        header[data-testid="stHeader"] {{
            display: none !important;
        }}
        footer {{
            visibility: hidden !important;
        }}
        .block-container {{
            padding-top: 0.35rem !important;
            padding-bottom: 3.6rem !important;
            max-width: 680px !important;
        }}
        .eb-app-header {{
            text-align: center;
            padding: 0.2rem 0 0.35rem;
            margin-bottom: 0;
        }}
        .eb-app-header h1 {{
            font-size: 1.2rem;
            margin: 0;
            color: {ACCENT};
            font-family: 'Noto Serif SC', serif !important;
        }}
        .eb-app-header p {{
            margin: 0.15rem 0 0;
            font-size: 0.8rem;
            color: #64748B;
        }}
        [data-testid="stVerticalBlock"] > div {{
            gap: 0.35rem !important;
        }}
        h1 {{
            font-size: 1.35rem !important;
            padding-top: 0 !important;
            margin-bottom: 0.15rem !important;
        }}
        .stCaption, [data-testid="stCaptionContainer"] {{
            margin-bottom: 0.25rem !important;
        }}
        /* 底部导航：三键单行横排 */
        section.main div.block-container > div > div[data-testid="stVerticalBlock"]:last-child {{
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            max-width: 680px !important;
            margin: 0 auto !important;
            background: rgba(249, 248, 246, 0.98) !important;
            border-top: 1px solid rgba(141, 163, 153, 0.28) !important;
            padding: 0.35rem 0.4rem calc(0.35rem + env(safe-area-inset-bottom)) !important;
            z-index: 999999 !important;
            box-shadow: 0 -4px 18px rgba(30, 41, 59, 0.06) !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"]:last-child [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            gap: 0.25rem !important;
            align-items: stretch !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"]:last-child [data-testid="column"] {{
            flex: 1 !important;
            min-width: 0 !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"]:last-child button {{
            border-radius: 10px !important;
            min-height: 2.15rem !important;
            height: auto !important;
            font-size: 0.68rem !important;
            padding: 0.35rem 0.2rem !important;
            white-space: nowrap !important;
            width: 100% !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"]:last-child button[kind="secondary"] {{
            background: rgba(255,255,255,0.6) !important;
            color: {TEXT} !important;
            border: 1px solid rgba(141, 163, 153, 0.2) !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"]:last-child button[kind="primary"] {{
            background: rgba(141, 163, 153, 0.18) !important;
            color: {ACCENT} !important;
            border: 1px solid rgba(141, 163, 153, 0.45) !important;
            font-weight: 600 !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"]:last-child button[kind="primary"]::before {{
            color: {ACCENT} !important;
        }}
        @media (max-width: 640px) {{
            .block-container {{
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }}
            section.main div.block-container > div > div[data-testid="stVerticalBlock"]:last-child button {{
                font-size: 0.62rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_header(today: str, favorited_count: int) -> None:
    st.markdown(
        f"""
        <div class="eb-app-header">
            <h1 style="text-align: center; font-family: 'Noto Serif SC', serif; color: #1E293B;"><i class="fa-solid fa-seedling" style="color: #8DA399; margin-right: 15px;"></i>简愈一人食</h1>
            <p>今日 {today} · 收藏 {favorited_count} 道</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bottom_nav() -> None:
    if "current_page" not in st.session_state:
        st.session_state.current_page = "morning"

    cols = st.columns(3, gap="small")
    for col, (page_id, label) in zip(cols, NAV_ITEMS):
        with col:
            is_active = st.session_state.current_page == page_id
            if st.button(
                label,
                key=f"nav_{page_id}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state.current_page = page_id
                st.rerun()
