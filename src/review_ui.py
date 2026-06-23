"""Review page UI helpers."""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import quote

import streamlit as st

from src.nav_params import append_nav_params


def dish_favorite_html(menu_id: str) -> str:
    """Heart + 收藏 on the same line as the dish title (HTML link)."""
    key = f"review_{menu_id}_fav_dish"
    active = bool(st.session_state.get(key, False))
    heart = "❤️" if active else "🤍"
    page = st.session_state.get("current_page", "night")
    href = append_nav_params(f"?nav={quote(page)}&review_fav={quote(menu_id)}")
    active_cls = " active" if active else ""
    return (
        f'<a class="eb-fav-link{active_cls}" href="{href}">'
        f'<span class="eb-fav-heart">{heart}</span>收藏</a>'
    )


def render_dish_header_with_favorite(meal_type: str, dish_name: str, menu_id: str) -> None:
    fav = dish_favorite_html(menu_id)
    st.markdown(
        f'<div class="eb-dish-header-line">'
        f'<span class="eb-dish-name">{meal_type}：{dish_name}</span>'
        f"{fav}</div>",
        unsafe_allow_html=True,
    )


def render_score_picker(
    title: str,
    caption: str,
    session_key: str,
    *,
    btn_prefix: str,
    on_pick: Callable[[], None] | None = None,
) -> None:
    """Five score chips in one row — reliable inside bordered cards on mobile."""
    st.markdown(f'<p class="eb-score-label">{title}</p>', unsafe_allow_html=True)
    st.caption(caption)
    current = st.session_state.get(session_key)
    cols = st.columns(5, gap="small")
    for score in range(1, 6):
        with cols[score - 1]:
            selected = current == score

            def _pick(*, s: int = score) -> None:
                st.session_state[session_key] = s
                if on_pick:
                    on_pick()

            st.button(
                str(score),
                key=f"{btn_prefix}_{score}",
                use_container_width=True,
                type="primary" if selected else "secondary",
                on_click=_pick,
            )
