"""Theme_3 visual system — cream / sage / serif."""

from __future__ import annotations

import streamlit as st

FONT_AWESOME_CDN = (
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">'
)

GOOGLE_FONTS = (
    '<link rel="stylesheet" '
    'href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700&'
    'family=Noto+Serif+SC:wght@400;600;700&display=swap">'
)

ACCENT = "#8DA399"
BG = "#F9F8F6"
TEXT = "#1E293B"
LIFESTYLE_PLACEHOLDER_URL = (
    "http://googleusercontent.com/image_collection/image_retrieval/13967363910131595220"
)

# aria-label (button text) -> Font Awesome solid unicode
ICON_BUTTON_MAP: dict[str, str] = {
    "菜单": "\\f185",
    "回顾": "\\f06c",
    "分享": "\\f1e0",
    "晨间餐饮": "\\f185",
    "晚间回顾": "\\f06c",
    "收藏分享": "\\f1e0",
    "生成菜单": "\\f2e7",
    "换套菜单": "\\f074",
    "换一套": "\\f074",
    "记录": "\\f0c7",
    "确认今日就餐计划": "\\f00c",
    "生成海报": "\\f030",       # camera
    "保存至本地": "\\f019",     # download
    "复制分享指南": "\\f0c1",   # link
    "确认导入": "\\f56f",      # file-import
    "完成今日回顾，去生成日志": "\\f186",  # moon
    "加入": "\\f055",           # circle-plus
}


def _icon_button_css() -> str:
    rules = []
    for label, code in ICON_BUTTON_MAP.items():
        rules.append(
            f"""
        .stButton > button[aria-label="{label}"]::before {{
            font-family: "Font Awesome 6 Free";
            font-weight: 900;
            content: "{code}";
            margin-right: 0.32em;
            color: {ACCENT};
        }}
        """
        )
    # remove buttons: aria-label starts with "移除"
    rules.append(
        f"""
        .stButton > button[aria-label^="移除"]::before {{
            font-family: "Font Awesome 6 Free";
            font-weight: 900;
            content: "\\f057";
            margin-right: 0.28em;
            color: {ACCENT};
        }}
        .stButton > button[aria-label^="生成口令"]::before {{
            font-family: "Font Awesome 6 Free";
            font-weight: 900;
            content: "\\f1e0";
            margin-right: 0.28em;
            color: {ACCENT};
        }}
        .stDownloadButton > button[aria-label="保存至本地"]::before {{
            font-family: "Font Awesome 6 Free";
            font-weight: 900;
            content: "\\f019";
            margin-right: 0.32em;
            color: {ACCENT};
        }}
        .stDownloadButton > button {{
            white-space: nowrap !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        """
    )
    return "\n".join(rules)


def inject_theme_assets() -> None:
    st.markdown(FONT_AWESOME_CDN, unsafe_allow_html=True)
    st.markdown(GOOGLE_FONTS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&family=Noto+Serif+SC:wght@400;600;700&display=swap');

        :root {{
            --eb-bg: {BG};
            --eb-accent: {ACCENT};
            --eb-text: {TEXT};
            --eb-accent-soft: rgba(141, 163, 153, 0.12);
            --eb-accent-border: rgba(141, 163, 153, 0.35);
        }}

        html, body, [class*="css"] {{
            font-family: 'Lato', sans-serif !important;
            color: {TEXT} !important;
        }}

        h1, h2, h3, h4, h5, h6,
        .eb-page-title, .eb-app-header h1,
        .eb-section-title {{
            font-family: 'Noto Serif SC', serif !important;
            color: {TEXT} !important;
        }}

        .stApp {{
            background-color: {BG} !important;
        }}

        .eb-app-header h1 {{
            color: {ACCENT} !important;
        }}

        .eb-app-header p,
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: #64748B !important;
        }}

        .eb-page-title {{
            font-size: 1.45rem;
            font-weight: 600;
            margin: 0 0 0.15rem 0;
            line-height: 1.35;
        }}

        .eb-page-title i {{
            color: {ACCENT};
            margin-right: 0.45rem;
        }}

        .eb-section-title {{
            font-size: 1.05rem;
            font-weight: 600;
            margin: 0.75rem 0 0.35rem;
        }}

        .eb-section-title i {{
            color: {ACCENT};
            margin-right: 0.35rem;
        }}

        /* 全站按钮：图标在文字前，单行横向 */
        .stButton > button {{
            font-family: 'Lato', sans-serif !important;
            white-space: nowrap !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.15rem !important;
            line-height: 1.2 !important;
        }}

        {_icon_button_css()}

        .stButton > button[kind="primary"] {{
            background-color: {ACCENT} !important;
            border-color: {ACCENT} !important;
            color: #fff !important;
        }}

        .stButton > button[kind="primary"]::before {{
            color: #fff !important;
        }}

        .stButton > button[kind="primary"]:hover {{
            background-color: #7a9188 !important;
            border-color: #7a9188 !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: var(--eb-accent-border) !important;
            background: rgba(255, 255, 255, 0.55) !important;
            border-radius: 12px !important;
        }}

        [data-testid="stTabs"] [data-testid="stTab"] {{
            font-family: 'Noto Serif SC', serif !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_title(icon_class: str, title: str, caption: str = "") -> None:
    st.markdown(
        f'<p class="eb-page-title"><i class="fa-solid {icon_class}"></i>{title}</p>',
        unsafe_allow_html=True,
    )
    if caption:
        st.caption(caption)


def section_title(icon_class: str, title: str) -> None:
    st.markdown(
        f'<p class="eb-section-title"><i class="fa-solid {icon_class}"></i>{title}</p>',
        unsafe_allow_html=True,
    )
