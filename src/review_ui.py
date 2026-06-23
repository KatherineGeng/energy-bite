"""Review page UI helpers."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def render_dish_header_with_favorite(
    meal_type: str,
    dish_name: str,
    menu_id: str,
    *,
    on_toggle: Callable[[], None] | None = None,
) -> None:
    """Dish title + favorite toggle via st.button (keeps scores in session)."""
    key = f"review_{menu_id}_fav_dish"
    active = bool(st.session_state.get(key, False))
    heart = "❤️" if active else "🤍"

    col_title, col_fav = st.columns([8, 2], gap="small")
    with col_title:
        st.markdown(
            f'<span class="eb-dish-name">{meal_type}：{dish_name}</span>',
            unsafe_allow_html=True,
        )
    with col_fav:
        st.button(
            f"{heart} 收藏",
            key=f"fav_btn_{menu_id}",
            use_container_width=True,
            on_click=on_toggle,
        )


def render_score_picker(
    title: str,
    caption: str,
    session_key: str,
    *,
    btn_prefix: str = "",
) -> None:
    """Five-point horizontal radio — matches 4.12.1 mobile layout."""
    del btn_prefix
    st.markdown(f'<p class="eb-score-label">{title}</p>', unsafe_allow_html=True)
    st.caption(caption)
    st.radio(
        title,
        options=[1, 2, 3, 4, 5],
        horizontal=True,
        format_func=str,
        label_visibility="collapsed",
        key=session_key,
        index=None,
    )
