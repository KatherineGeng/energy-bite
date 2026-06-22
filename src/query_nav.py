"""URL query-param helpers for HTML navigation (minimal deps)."""

from __future__ import annotations

import streamlit as st


def clear_query_key(key: str) -> None:
    remaining = {k: v for k, v in st.query_params.items() if k != key}
    st.query_params.from_dict(remaining)


def clear_query_action() -> None:
    clear_query_key("act")


def clear_meal_query() -> None:
    remaining = {k: v for k, v in st.query_params.items() if k not in ("meal_act", "meal", "mid")}
    st.query_params.from_dict(remaining)


def qp_first(key: str) -> str | None:
    val = st.query_params.get(key)
    if isinstance(val, list):
        return val[0] if val else None
    return val


def pop_query_param(key: str) -> str | None:
    """Read a query param once and remove it from the URL immediately."""
    val = qp_first(key)
    if val:
        clear_query_key(key)
    return val


def apply_query_nav(valid_pages: set[str]) -> None:
    export_tab = qp_first("export_tab")
    if export_tab:
        st.session_state.export_tab_key = export_tab

    nav = st.query_params.get("nav")
    if isinstance(nav, list):
        nav = nav[0] if nav else None
    if not nav or nav not in valid_pages:
        return
    page_changed = st.session_state.get("current_page") != nav
    st.session_state.current_page = nav
    if page_changed:
        st.rerun()
