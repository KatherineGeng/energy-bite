"""Mobile-first layout helpers for 简愈一人食."""

from __future__ import annotations

import streamlit as st

from src.constants import APP_VERSION
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
        *, *::before, *::after {{
            box-sizing: border-box !important;
        }}
        html {{
            -webkit-text-size-adjust: 100%;
        }}
        html, body {{
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            overflow-x: clip !important;
        }}
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        section.main,
        section.main > div,
        .block-container {{
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: clip !important;
        }}
        .stApp {{
            overflow-x: clip !important;
        }}
        /* 隐藏 Streamlit 右下角浮动控件 */
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
            pointer-events: none !important;
        }}
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        header[data-testid="stHeader"],
        footer {{
            display: none !important;
        }}
        .block-container {{
            padding-top: 0.25rem !important;
            padding-bottom: calc(4.8rem + env(safe-area-inset-bottom)) !important;
            padding-left: max(0.75rem, env(safe-area-inset-left)) !important;
            padding-right: max(0.75rem, env(safe-area-inset-right)) !important;
        }}
        /* 长文本换行，避免撑破屏幕 */
        p, span, label, .stMarkdown, [data-testid="stMarkdownContainer"] {{
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
        }}
        /* 仅对「双键操作行」和「底部导航行」强制横排 */
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="生成菜单"]),
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="晨间餐饮"]),
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="加入"]) {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            max-width: 100% !important;
            gap: 0.35rem !important;
        }}
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="生成菜单"]) [data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="晨间餐饮"]) [data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(button[aria-label="加入"]) [data-testid="column"] {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            width: 0 !important;
        }}
        .stButton > button {{
            width: 100% !important;
            max-width: 100% !important;
            font-size: 0.78rem !important;
            padding: 0.42rem 0.2rem !important;
            white-space: normal !important;
            line-height: 1.15 !important;
        }}
        div[data-testid="stSelectbox"],
        div[data-testid="stSelectbox"] > div {{
            width: 100% !important;
            max-width: 100% !important;
        }}
        div[data-testid="stRadio"] > div {{
            flex-wrap: wrap !important;
            gap: 0.2rem !important;
        }}
        /* 底部导航固定 + 去掉文档流占位，防止横向溢出 */
        div[data-testid="element-container"]:has(button[aria-label="晨间餐饮"]) {{
            position: fixed !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            z-index: 999999 !important;
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0.35rem max(0.75rem, env(safe-area-inset-left)) calc(0.4rem + env(safe-area-inset-bottom)) max(0.75rem, env(safe-area-inset-right)) !important;
            background: rgba(249, 248, 246, 0.98) !important;
            border-top: 1px solid rgba(141, 163, 153, 0.28) !important;
            box-shadow: 0 -4px 16px rgba(30, 41, 59, 0.06) !important;
        }}
        div[data-testid="element-container"]:has(button[aria-label="晨间餐饮"]) [data-testid="stHorizontalBlock"] {{
            margin: 0 !important;
            padding: 0 !important;
        }}
        div[data-testid="element-container"]:has(button[aria-label="晨间餐饮"]) button {{
            border-radius: 10px !important;
            min-height: 2.1rem !important;
            font-size: 0.62rem !important;
        }}
        div[data-testid="element-container"]:has(button[aria-label="晨间餐饮"]) button[kind="secondary"] {{
            background: rgba(255,255,255,0.85) !important;
            color: {TEXT} !important;
            border: 1px solid rgba(141, 163, 153, 0.25) !important;
        }}
        div[data-testid="element-container"]:has(button[aria-label="晨间餐饮"]) button[kind="primary"] {{
            background: rgba(141, 163, 153, 0.2) !important;
            color: {ACCENT} !important;
            border: 1px solid rgba(141, 163, 153, 0.45) !important;
            font-weight: 600 !important;
        }}
        div[data-testid="element-container"]:has(button[aria-label="晨间餐饮"]) button[kind="primary"]::before {{
            color: {ACCENT} !important;
        }}
        .eb-version-badge {{
            text-align: center;
            font-size: 0.72rem;
            color: {ACCENT};
            font-weight: 700;
            margin: -0.5rem 0 0.4rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_header(today: str, favorited_count: int) -> None:
    st.markdown(
        "<h2 style='text-align:center;color:#1E293B;margin:0 0 0.25rem;font-size:1.35rem;'>"
        "<i class='fa-solid fa-leaf' style='color:#8DA399;'></i> 简愈一人食</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="eb-version-badge">版本 {APP_VERSION}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;font-size:0.78rem;color:#64748B;margin:0 0 0.5rem;'>"
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
