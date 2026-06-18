"""Mobile-first layout helpers for 简愈一人食."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.constants import APP_VERSION
from src.theme import ACCENT, TEXT

NAV_ITEMS = [
    ("morning", "晨间餐饮"),
    ("night", "晚间回顾"),
    ("export", "收藏分享"),
]

_ROOT = Path(__file__).resolve().parent.parent
_FAVICON = _ROOT / "favicon.png"
if not _FAVICON.exists():
    _FAVICON = _ROOT / "assets" / "favicon.png"
_APPLE_TOUCH_ICON = _ROOT / "apple-touch-icon.png"
if not _APPLE_TOUCH_ICON.exists():
    _APPLE_TOUCH_ICON = _ROOT / "assets" / "apple-touch-icon.png"


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
        /* 强制所有 st.columns 在手机上保持横排 */
        div[data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            max-width: 100% !important;
            gap: 0.35rem !important;
        }}
        div[data-testid="column"] {{
            flex: 1 1 0% !important;
            min-width: 0 !important;
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
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 0.15rem !important;
            width: 100% !important;
        }}
        div[data-testid="stRadio"] label {{
            margin-right: 0.25rem !important;
            font-size: 0.85rem !important;
        }}
        /* 底部导航固定栏（app.py 最后一个 block = st.radio 导航） */
        section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child {{
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            z-index: 999999 !important;
            background: rgba(249, 248, 246, 0.98) !important;
            border-top: 1px solid rgba(141, 163, 153, 0.28) !important;
            padding: 0.35rem 0.5rem calc(0.45rem + env(safe-area-inset-bottom)) !important;
            box-shadow: 0 -4px 18px rgba(30, 41, 59, 0.06) !important;
            max-width: 100vw !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child div[data-testid="stRadio"] > div {{
            flex-wrap: nowrap !important;
            justify-content: space-between !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child div[data-testid="stRadio"] label {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0.35rem 0.15rem !important;
            font-size: 0.68rem !important;
            text-align: center !important;
            justify-content: center !important;
            background: rgba(255,255,255,0.6) !important;
            border: 1px solid rgba(141, 163, 153, 0.2) !important;
            border-radius: 10px !important;
            color: {TEXT} !important;
        }}
        section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child div[data-testid="stRadio"] label:has(input:checked) {{
            background: rgba(141, 163, 153, 0.18) !important;
            border-color: rgba(141, 163, 153, 0.45) !important;
            color: {ACCENT} !important;
            font-weight: 600 !important;
        }}
        .eb-version-badge {{
            text-align: center;
            font-size: 0.72rem;
            color: {ACCENT};
            font-weight: 700;
            letter-spacing: 0.04em;
            margin: -0.8rem 0 0.6rem;
        }}
        @media (max-width: 640px) {{
            .stButton > button {{
                font-size: 0.78rem !important;
            }}
            section.main div.block-container > div > div[data-testid="stVerticalBlock"] > div:last-child div[data-testid="stRadio"] label {{
                font-size: 0.62rem !important;
                padding: 0.3rem 0.1rem !important;
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
        f'<p class="eb-version-badge">版本 {APP_VERSION}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;font-size:0.8rem;color:#64748B;margin-top:-0.4rem;margin-bottom:0.5rem;'>"
        f"今日 {today} · 收藏 {favorited_count} 道</p>",
        unsafe_allow_html=True,
    )


def render_bottom_nav() -> None:
    if "current_page" not in st.session_state:
        st.session_state.current_page = "morning"

    label_by_id = {page_id: label for page_id, label in NAV_ITEMS}
    id_by_label = {label: page_id for page_id, label in NAV_ITEMS}
    labels = [label for _, label in NAV_ITEMS]

    current_id = st.session_state.current_page
    st.session_state.eb_bottom_nav = label_by_id.get(current_id, labels[0])

    def _on_nav_change() -> None:
        st.session_state.current_page = id_by_label[st.session_state.eb_bottom_nav]

    st.radio(
        "页面导航",
        options=labels,
        horizontal=True,
        label_visibility="collapsed",
        key="eb_bottom_nav",
        on_change=_on_nav_change,
    )
