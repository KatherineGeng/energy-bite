"""Review page UI helpers."""

from __future__ import annotations

from urllib.parse import quote

import streamlit as st

from src.nav_params import append_nav_params


def dish_favorite_html(menu_id: str) -> str:
    """Inline heart on the dish title row — no button box."""
    key = f"review_{menu_id}_fav_dish"
    active = bool(st.session_state.get(key, False))
    heart = "❤️" if active else "🤍"
    page = st.session_state.get("current_page", "night")
    href = append_nav_params(f"?nav={quote(page)}&review_fav={quote(menu_id)}")
    active_cls = " active" if active else ""
    return (
        f'<a class="eb-fav-link{active_cls}" href="{href}" aria-label="收藏">'
        f'<span class="eb-fav-heart">{heart}</span></a>'
    )


def render_dish_header_with_favorite(meal_type: str, dish_name: str, menu_id: str) -> None:
    fav = dish_favorite_html(menu_id)
    st.markdown(
        f'<div class="eb-dish-header-line">'
        f'<span class="eb-dish-name">{meal_type}：{dish_name}</span>'
        f"{fav}</div>",
        unsafe_allow_html=True,
    )
