"""Review page UI helpers."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from src.database import load_favorites_dishes


def dish_favorited(menu_id: str, today: str) -> bool:
    key = f"review_{menu_id}_fav_dish"
    if key in st.session_state:
        return bool(st.session_state[key])
    df = load_favorites_dishes()
    if df.empty:
        return False
    return not df[(df["menu_id"] == menu_id) & (df["date"] == today)].empty


def render_dish_header_with_favorite(
    meal_type: str,
    dish_name: str,
    menu_id: str,
    today: str,
    *,
    on_toggle: Callable[[], None],
) -> None:
    """Dish title + heart/收藏 on one row — Streamlit button, fragment rerun only."""
    active = dish_favorited(menu_id, today)
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


def render_score_picker(
    title: str,
    caption: str,
    session_key: str,
    *,
    btn_prefix: str,
    on_pick: Callable[[], None] | None = None,
) -> None:
    """Five score chips in one row — on_click only reruns the parent fragment."""
    st.markdown(f'<p class="eb-score-label">{title}</p>', unsafe_allow_html=True)
    st.caption(caption)
    current = st.session_state.get(session_key)
    cols = st.columns(5, gap="small")
    for score in range(1, 6):
        with cols[score - 1]:

            def _pick(*, picked: int = score) -> None:
                st.session_state[session_key] = picked
                if on_pick:
                    on_pick()

            st.button(
                str(score),
                key=f"{btn_prefix}_{score}",
                use_container_width=True,
                type="primary" if current == score else "secondary",
                on_click=_pick,
            )
