"""URL query-param helpers for HTML navigation (minimal deps)."""

from __future__ import annotations

import streamlit as st


def clear_query_key(key: str) -> None:
    remaining = {k: v for k, v in st.query_params.items() if k != key}
    st.query_params.from_dict(remaining)


def clear_query_action() -> None:
    clear_query_key("act")


def apply_query_nav(valid_pages: set[str]) -> None:
    nav = st.query_params.get("nav")
    if isinstance(nav, list):
        nav = nav[0] if nav else None
    if not nav or nav not in valid_pages:
        return
    changed = st.session_state.get("current_page") != nav
    st.session_state.current_page = nav
    clear_query_key("nav")
    if changed:
        st.rerun()
