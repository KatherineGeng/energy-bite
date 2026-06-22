"""Theme — system fonts, senior-friendly sizing."""

from __future__ import annotations

import streamlit as st

ACCENT = "#8DA399"
BG = "#F9F8F6"
TEXT = "#1E293B"
LIFESTYLE_PLACEHOLDER_URL = (
    "https://images.unsplash.com/photo-1498837167922-ddd27525cd41?w=800&q=80"
)

_FONT_STACK = '-apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif'
_SERIF_STACK = '"PingFang SC", "Noto Serif SC", "Songti SC", serif'


def inject_theme_assets() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --eb-bg: {BG};
            --eb-accent: {ACCENT};
            --eb-text: {TEXT};
            --eb-accent-soft: rgba(141, 163, 153, 0.12);
            --eb-accent-border: rgba(141, 163, 153, 0.35);
        }}

        html, body, [class*="css"], .stApp {{
            font-family: {_FONT_STACK} !important;
            font-size: 18px !important;
            color: {TEXT} !important;
            background-color: {BG} !important;
        }}

        h1, h2, h3, h4, h5, h6,
        .eb-page-title, .eb-section-title {{
            font-family: {_SERIF_STACK} !important;
            color: {TEXT} !important;
        }}

        .eb-page-title {{
            font-size: 1.65rem;
            font-weight: 600;
            margin: 0 0 0.2rem 0;
            line-height: 1.35;
        }}

        .eb-section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0.85rem 0 0.45rem;
        }}

        .stButton > button {{
            font-family: {_FONT_STACK} !important;
            font-size: 1.05rem !important;
            min-height: 3rem !important;
            padding: 0.55rem 1rem !important;
            white-space: nowrap !important;
        }}

        .stButton > button[kind="primary"] {{
            background-color: {ACCENT} !important;
            border-color: {ACCENT} !important;
            color: #fff !important;
        }}

        .stCaption, [data-testid="stCaptionContainer"] {{
            font-size: 1rem !important;
        }}

        label, .stRadio label, .stCheckbox label {{
            font-size: 1.05rem !important;
        }}

        input, textarea, select {{
            font-size: 1.05rem !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: var(--eb-accent-border) !important;
            background: rgba(255, 255, 255, 0.55) !important;
            border-radius: 12px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_title(icon: str, title: str, caption: str = "") -> None:
    del icon
    st.markdown(f'<p class="eb-page-title">{title}</p>', unsafe_allow_html=True)
    if caption:
        st.caption(caption)


def section_title(icon: str, title: str) -> None:
    del icon
    st.markdown(f'<p class="eb-section-title">{title}</p>', unsafe_allow_html=True)
