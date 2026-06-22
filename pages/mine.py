"""我的 — 日历回顾 + 折叠式收藏."""

from __future__ import annotations

import streamlit as st

from src.database import init_database
from src.favorites_ui import render_collapsible_favorites
from src.menu_review_ui import render_calendar_menu_review
from src.session_hydrate import hydrate_today_state


def _inject_mine_css() -> None:
    st.markdown(
        """
        <style>
        .eb-mine-panel {
            margin: 0.55rem 0 0.85rem;
            padding: 0.75rem 0.65rem 0.35rem;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.55);
            border: 1px solid rgba(141, 163, 153, 0.18);
        }
        .eb-mine-section-title {
            font-size: 1rem;
            font-weight: 600;
            margin: 0.15rem 0 0.55rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    init_database()
    hydrate_today_state()
    _inject_mine_css()

    st.markdown('<p class="eb-mine-section-title">📅 日历菜单回顾</p>', unsafe_allow_html=True)
    render_calendar_menu_review(nav_page="mine")

    st.markdown('<p class="eb-mine-section-title">🌟 我的收藏</p>', unsafe_allow_html=True)
    render_collapsible_favorites(key_prefix="mine")
