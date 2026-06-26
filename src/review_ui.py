"""Review page UI — HTML chips (5.0.19 layout) + query-param clicks."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any
from urllib.parse import quote

import streamlit as st

from src.database import load_favorites_dishes
from src.review_nav_state import chip_nav_href


def dish_favorited(menu_id: str, today: str) -> bool:
    key = f"review_{menu_id}_fav_dish"
    if key in st.session_state:
        return bool(st.session_state[key])
    df = load_favorites_dishes()
    if df.empty:
        return False
    return not df[(df["menu_id"] == menu_id) & (df["date"] == today)].empty


def dish_favorite_html(menu_id: str, today: str) -> str:
    """Heart + 收藏 on the same line as the dish title (HTML link)."""
    active = dish_favorited(menu_id, today)
    st.session_state[f"review_{menu_id}_fav_dish"] = active
    heart = "❤️" if active else "🤍"
    page = st.session_state.get("current_page", "night")
    href = chip_nav_href(f"?nav={quote(page)}&review_fav={quote(menu_id)}")
    active_cls = " active" if active else ""
    return (
        f'<a class="eb-fav-link{active_cls}" href="{href}">'
        f'<span class="eb-fav-heart">{heart}</span>收藏</a>'
    )


def render_dish_header_with_favorite(meal_type: str, dish_name: str, menu_id: str, today: str) -> None:
    fav = dish_favorite_html(menu_id, today)
    st.markdown(
        f'<div class="eb-dish-header-line">'
        f'<span class="eb-dish-name">{meal_type}：{dish_name}</span>'
        f"{fav}</div>",
        unsafe_allow_html=True,
    )


def render_score_picker_html(
    title: str,
    caption: str,
    session_key: str,
    menu_id: str,
    field: str,
    today: str,
) -> None:
    """Five score chips in one HTML row — stable on mobile (no st.columns)."""
    current = st.session_state.get(session_key)
    page = st.session_state.get("current_page", "night")
    chips: list[str] = []
    for score in range(1, 6):
        selected = " selected" if current == score else ""
        token = f"{menu_id}:{field}:{score}"
        href = chip_nav_href(f"?nav={quote(page)}&review_score={quote(token)}")
        chips.append(f'<a class="eb-score-chip{selected}" href="{href}">{score}</a>')
    st.markdown(f'<p class="eb-score-label">{title}</p>', unsafe_allow_html=True)
    st.caption(caption)
    st.markdown(f'<div class="eb-score-row">{"".join(chips)}</div>', unsafe_allow_html=True)


def render_option_picker_html(
    title: str,
    caption: str,
    session_key: str,
    options: Sequence[Any],
    param_field: str,
    *,
    format_label: Callable[[Any], str] | None = None,
) -> None:
    """Horizontal option chips — same row style as score picker (morning questions)."""
    current = st.session_state.get(session_key)
    page = st.session_state.get("current_page", "night")
    chips: list[str] = []
    for opt in options:
        label = format_label(opt) if format_label else str(opt)
        selected = " selected" if current == opt else ""
        token = f"{param_field}:{opt}"
        href = chip_nav_href(f"?nav={quote(page)}&morning_pick={quote(token)}")
        chips.append(f'<a class="eb-score-chip{selected}" href="{href}">{label}</a>')
    st.markdown(f'<p class="eb-score-label">{title}</p>', unsafe_allow_html=True)
    if caption:
        st.caption(caption)
    st.markdown(f'<div class="eb-score-row">{"".join(chips)}</div>', unsafe_allow_html=True)
