"""Review page UI helpers."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def render_dish_header_with_favorite(
    meal_type: str,
    dish_name: str,
    menu_id: str,
    *,
    on_toggle: Callable[[], None],
) -> None:
    """Dish title row + inline heart/收藏 toggle (Streamlit button, no page reload)."""
    key = f"review_{menu_id}_fav_dish"
    active = bool(st.session_state.get(key, False))
    heart = "❤️" if active else "🤍"

    col_title, col_fav = st.columns([7, 3], gap="small")
    with col_title:
        st.markdown(
            f'<span class="eb-dish-name">{meal_type}：{dish_name}</span>',
            unsafe_allow_html=True,
        )
    with col_fav:
        st.button(
            f"{heart} 收藏",
            key=f"fav_btn_{menu_id}",
            type="primary" if active else "secondary",
            on_click=on_toggle,
            use_container_width=True,
        )
