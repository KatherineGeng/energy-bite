"""Review page UI — fast fragment pills (5.0.19 look) + HTML fallback."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

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
    """Dish title left, heart+收藏 right — same row as 5.0.19."""
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


def render_score_picker_html(
    title: str,
    caption: str,
    session_key: str,
    menu_id: str,
    field: str,
    today: str,
) -> None:
    """Legacy HTML href chips — full page reload; tests only."""
    from urllib.parse import quote

    from src.review_nav_state import chip_nav_href

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
    """Legacy HTML href chips — full page reload; tests only."""
    from urllib.parse import quote

    from src.review_nav_state import chip_nav_href

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


def _uses_fast_pills() -> bool:
    return hasattr(st, "pills")


def _pick_handler(session_key: str, value: Any, on_pick: Callable[[], None] | None) -> Callable[[], None]:
    def _handler() -> None:
        st.session_state[session_key] = value
        if on_pick:
            on_pick()

    return _handler


def _render_score_buttons(session_key: str, on_pick: Callable[[], None] | None) -> None:
    current = st.session_state.get(session_key)
    st.markdown('<div class="eb-review-picks">', unsafe_allow_html=True)
    cols = st.columns(5, gap="small")
    for col, score in zip(cols, range(1, 6)):
        with col:
            st.button(
                str(score),
                key=f"{session_key}__chip_{score}",
                type="primary" if current == score else "secondary",
                on_click=_pick_handler(session_key, score, on_pick),
                use_container_width=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_option_buttons(
    session_key: str,
    options: Sequence[Any],
    *,
    format_label: Callable[[Any], str] | None,
    on_pick: Callable[[], None] | None,
) -> None:
    current = st.session_state.get(session_key)
    st.markdown('<div class="eb-review-picks">', unsafe_allow_html=True)
    cols = st.columns(len(options), gap="small")
    for col, opt in zip(cols, options):
        label = format_label(opt) if format_label else str(opt)
        with col:
            st.button(
                label,
                key=f"{session_key}__chip_{opt}",
                type="primary" if current == opt else "secondary",
                on_click=_pick_handler(session_key, opt, on_pick),
                use_container_width=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def render_score_picker(
    title: str,
    caption: str,
    session_key: str,
    *,
    on_pick: Callable[[], None] | None = None,
) -> None:
    """Horizontal 1–5 chips; st.pills in @st.fragment avoids full-page reload."""
    st.markdown(f'<p class="eb-score-label">{title}</p>', unsafe_allow_html=True)
    if caption:
        st.caption(caption)
    if _uses_fast_pills():
        st.markdown('<div class="eb-review-picks">', unsafe_allow_html=True)
        st.pills(
            title,
            options=[1, 2, 3, 4, 5],
            format_func=str,
            selection_mode="single",
            key=session_key,
            label_visibility="collapsed",
            on_change=on_pick,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        _render_score_buttons(session_key, on_pick)


def render_option_picker(
    title: str,
    caption: str,
    session_key: str,
    options: Sequence[Any],
    *,
    format_label: Callable[[Any], str] | None = None,
    on_pick: Callable[[], None] | None = None,
) -> None:
    """Horizontal option chips — same look, fragment-fast via st.pills."""
    opts = list(options)
    st.markdown(f'<p class="eb-score-label">{title}</p>', unsafe_allow_html=True)
    if caption:
        st.caption(caption)
    if _uses_fast_pills():
        st.markdown('<div class="eb-review-picks">', unsafe_allow_html=True)
        st.pills(
            title,
            options=opts,
            format_func=format_label or str,
            selection_mode="single",
            key=session_key,
            label_visibility="collapsed",
            on_change=on_pick,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        _render_option_buttons(session_key, opts, format_label=format_label, on_pick=on_pick)
