"""Review page UI helpers."""

from __future__ import annotations

import streamlit as st


def render_dish_favorite_heart(menu_id: str) -> None:
    """Heart toggle: hollow gray when off, solid red when on."""
    key = f"review_{menu_id}_fav_dish"
    active = bool(st.session_state.get(key, False))
    icon = "❤️" if active else "🤍"
    if st.button(icon, key=f"heart_{menu_id}", help="收藏此菜"):
        st.session_state[key] = not active
        st.rerun()
