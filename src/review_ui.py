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
    btn_prefix: str,
) -> None:
    """Five score buttons in one row — no radio wrap on mobile."""
    st.markdown(f'<p class="eb-score-label">{title}</p>', unsafe_allow_html=True)
    st.caption(caption)
    current = st.session_state.get(session_key)
    cols = st.columns(5, gap="small")
    for score in range(1, 6):
        with cols[score - 1]:
            selected = current == score
            if st.button(
                str(score),
                key=f"{btn_prefix}_{score}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state[session_key] = score
                st.rerun()
