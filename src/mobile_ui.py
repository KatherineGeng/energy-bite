"""Mobile-first layout helpers for 简愈一人食."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.theme import ACCENT, TEXT

NAV_ITEMS = [
    ("morning", "晨间餐饮"),
    ("night", "晚间回顾"),
    ("export", "收藏分享"),
]

_APPLE_TOUCH_ICON = Path(__file__).resolve().parent.parent / "assets" / "apple-touch-icon.png"
_FAVICON = Path(__file__).resolve().parent.parent / "assets" / "favicon.png"


def _apple_touch_icon_tag() -> str:
    tags = []
    if _FAVICON.exists():
        encoded = base64.b64encode(_FAVICON.read_bytes()).decode("ascii")
        tags.append(
            f'<link rel="icon" type="image/png" sizes="32x32" href="data:image/png;base64,{encoded}">'
        )
    if _APPLE_TOUCH_ICON.exists():
        encoded = base64.b64encode(_APPLE_TOUCH_ICON.read_bytes()).decode("ascii")
        tags.append(
            f'<link rel="apple-touch-icon" sizes="180x180" href="data:image/png;base64,{encoded}">'
        )
    return "".join(tags)


def inject_mobile_css() -> None:
    icon_tags = _apple_touch_icon_tag()
    if icon_tags:
        st.markdown(icon_tags, unsafe_allow_html=True)

    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            overflow-x: hidden !important;
            max-width: 100vw !important;
        }}
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
        section.main {{
            overflow-x: hidden !important;
        }}
        .block-container {{
            padding-top: 0.35rem !important;
            padding-bottom: calc(5.5rem + env(safe-area-inset-bottom)) !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
            width: 100% !important;
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
        /* 双列按钮行：各占 50%，不溢出 */
        div[data-testid="stHorizontalBlock"] {{
            width: 100% !important;
            max-width: 100% !important;
            gap: 0.35rem !important;
        }}
        div[data-testid="column"] {{
            min-width: 0 !important;
            flex: 1 1 0 !important;
            width: auto !important;
        }}
        .stButton > button {{
            width: 100% !important;
            max-width: 100% !important;
            white-space: nowrap !important;
            font-size: 0.82rem !important;
            padding: 0.45rem 0.35rem !important;
        }}
        div[data-testid="stSelectbox"] {{
            width: 100% !important;
            max-width: 100% !important;
        }}
        div[data-testid="stRadio"] > div {{
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 0.15rem !important;
        }}
        div[data-testid="stRadio"] label {{
            margin-right: 0.25rem !important;
            font-size: 0.85rem !important;
        }}
        /* 底部导航：固定于屏幕底部（app.py 最后一个 block） */
        section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child {{
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            z-index: 999999 !important;
            background: rgba(249, 248, 246, 0.98) !important;
            border-top: 1px solid rgba(141, 163, 153, 0.28) !important;
            padding: 0.4rem 0.75rem calc(0.5rem + env(safe-area-inset-bottom)) !important;
            box-shadow: 0 -4px 18px rgba(30, 41, 59, 0.06) !important;
            max-width: 100vw !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child [data-testid="stHorizontalBlock"] {{
            flex-wrap: nowrap !important;
            gap: 0.25rem !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child button[kind="secondary"] {{
            background: rgba(255,255,255,0.6) !important;
            color: {TEXT} !important;
            border: 1px solid rgba(141, 163, 153, 0.2) !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child button[kind="primary"] {{
            background: rgba(141, 163, 153, 0.18) !important;
            color: {ACCENT} !important;
            border: 1px solid rgba(141, 163, 153, 0.45) !important;
            font-weight: 600 !important;
        }}
        @media (max-width: 640px) {{
            .stButton > button {{
                font-size: 0.78rem !important;
            }}
            section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child button {{
                font-size: 0.62rem !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_header(today: str, favorited_count: int) -> None:
    st.markdown(
        "<h2 style='text-align: center; color: #1E293B; margin-bottom: 30px;'>"
        "<i class='fa-solid fa-leaf' style='color: #8DA399;'></i> 简愈一人食</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;font-size:0.8rem;color:#64748B;margin-top:-1.2rem;margin-bottom:0.5rem;'>"
        f"今日 {today} · 收藏 {favorited_count} 道</p>",
        unsafe_allow_html=True,
    )


def render_bottom_nav() -> None:
    if "current_page" not in st.session_state:
        st.session_state.current_page = "morning"

    col1, col2, col3 = st.columns(3, gap="small")
    for col, (page_id, label) in zip((col1, col2, col3), NAV_ITEMS):
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
