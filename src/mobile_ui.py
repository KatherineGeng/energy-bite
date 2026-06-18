"""Mobile-first layout helpers for 简愈一人食."""

from __future__ import annotations

import base64
import json
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


def _pwa_head_tags() -> str:
    tags: list[str] = []
    if _FAVICON.exists():
        fav_b64 = base64.b64encode(_FAVICON.read_bytes()).decode("ascii")
        tags.append(
            f'<link rel="icon" type="image/png" sizes="32x32" '
            f'href="data:image/png;base64,{fav_b64}">'
        )
    if _APPLE_TOUCH_ICON.exists():
        touch_b64 = base64.b64encode(_APPLE_TOUCH_ICON.read_bytes()).decode("ascii")
        tags.append(
            f'<link rel="apple-touch-icon" sizes="180x180" '
            f'href="data:image/png;base64,{touch_b64}">'
        )
        manifest = {
            "name": "简愈一人食",
            "short_name": "简愈一人食",
            "icons": [
                {
                    "src": f"data:image/png;base64,{touch_b64}",
                    "sizes": "180x180",
                    "type": "image/png",
                    "purpose": "any maskable",
                }
            ],
            "display": "standalone",
            "theme_color": "#8DA399",
            "background_color": "#F9F8F6",
        }
        manifest_b64 = base64.b64encode(json.dumps(manifest, ensure_ascii=False).encode()).decode("ascii")
        tags.append(f'<link rel="manifest" href="data:application/manifest+json;base64,{manifest_b64}">')
    tags.append('<meta name="apple-mobile-web-app-title" content="简愈一人食">')
    tags.append('<meta name="theme-color" content="#8DA399">')
    return "".join(tags)


def inject_mobile_css() -> None:
    head_tags = _pwa_head_tags()
    if head_tags:
        st.markdown(head_tags, unsafe_allow_html=True)

    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            overflow-x: hidden !important;
            max-width: 100vw !important;
        }}
        /* 隐藏 Streamlit 右下角默认浮动控件（皇冠/设置等） */
        [data-testid="stToolbar"],
        [data-testid="stToolbarActions"],
        [data-testid="stAppDeployButton"],
        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"],
        [data-testid="stBottomBlockContainer"],
        .stAppDeployButton,
        #MainMenu,
        .viewerBadge_container,
        div[class*="viewerBadge"],
        button[kind="header"],
        [data-testid="baseButton-header"] {{
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
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
            display: none !important;
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
        /* 强制 st.columns 横排（覆盖 Streamlit 手机端竖排） */
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
            font-size: 0.78rem !important;
            padding: 0.4rem 0.25rem !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
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
        /* 底部导航：含三个 Tab 按钮的横排块固定于底部 */
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="晨间餐饮"]) {{
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            z-index: 999999 !important;
            background: rgba(249, 248, 246, 0.98) !important;
            border-top: 1px solid rgba(141, 163, 153, 0.28) !important;
            padding: 0.4rem 0.6rem calc(0.45rem + env(safe-area-inset-bottom)) !important;
            box-shadow: 0 -4px 18px rgba(30, 41, 59, 0.06) !important;
            max-width: 100vw !important;
            margin: 0 !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="晨间餐饮"]) button {{
            border-radius: 10px !important;
            min-height: 2.2rem !important;
            font-size: 0.65rem !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="晨间餐饮"]) button[kind="secondary"] {{
            background: rgba(255,255,255,0.6) !important;
            color: {TEXT} !important;
            border: 1px solid rgba(141, 163, 153, 0.2) !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="晨间餐饮"]) button[kind="primary"] {{
            background: rgba(141, 163, 153, 0.18) !important;
            color: {ACCENT} !important;
            border: 1px solid rgba(141, 163, 153, 0.45) !important;
            font-weight: 600 !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="晨间餐饮"]) button[kind="primary"]::before {{
            color: {ACCENT} !important;
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
            div[data-testid="stHorizontalBlock"]:has(button[aria-label="晨间餐饮"]) button {{
                font-size: 0.6rem !important;
                padding: 0.35rem 0.15rem !important;
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
