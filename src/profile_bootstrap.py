"""Restore profile token from browser localStorage (Streamlit-safe)."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from src.query_nav import qp_first


def restore_profile_from_browser() -> None:
    """If URL has no ebp but localStorage does, redirect to add ebp (keeps other params)."""
    if qp_first("ebp"):
        return
    if st.session_state.get("eb_browser_checked"):
        return

    components.html(
        """
        <script>
        (function () {
          try {
            var stored = localStorage.getItem("eb_profile");
            if (!stored) return;
            var u = new URL(window.parent.location.href);
            if (u.searchParams.get("ebp")) return;
            u.searchParams.set("ebp", stored);
            window.parent.location.replace(u.toString());
          } catch (e) {}
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )
    st.session_state.eb_browser_checked = True


def persist_profile_to_browser(token: str) -> None:
    safe = token.replace("\\", "\\\\").replace('"', '\\"')
    components.html(
        f"""
        <script>
        try {{
          localStorage.setItem("eb_profile", "{safe}");
        }} catch (e) {{}}
        </script>
        """,
        height=0,
        scrolling=False,
    )
