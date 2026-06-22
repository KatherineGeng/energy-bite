"""Restore profile/admin tokens from browser localStorage (Streamlit-safe)."""

from __future__ import annotations

import hashlib

import streamlit as st
import streamlit.components.v1 as components

from src.query_nav import qp_first


def admin_remember_token(password: str) -> str:
    if not password:
        return ""
    return hashlib.sha256(f"eb-admin:{password}".encode()).hexdigest()[:24]


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


def restore_admin_from_browser() -> None:
    """If admin was remembered in localStorage, redirect to add adm token."""
    if st.session_state.get("admin_authed"):
        return
    if qp_first("adm"):
        return
    if st.session_state.get("eb_admin_browser_checked"):
        return

    components.html(
        """
        <script>
        (function () {
          try {
            var stored = localStorage.getItem("eb_admin");
            if (!stored) return;
            var u = new URL(window.parent.location.href);
            if (u.searchParams.get("adm")) return;
            u.searchParams.set("adm", stored);
            window.parent.location.replace(u.toString());
          } catch (e) {}
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )
    st.session_state.eb_admin_browser_checked = True


def persist_admin_to_browser(token: str) -> None:
    safe = token.replace("\\", "\\\\").replace('"', '\\"')
    components.html(
        f"""
        <script>
        try {{
          localStorage.setItem("eb_admin", "{safe}");
        }} catch (e) {{}}
        </script>
        """,
        height=0,
        scrolling=False,
    )


def clear_admin_from_browser() -> None:
    components.html(
        """
        <script>
        try {
          localStorage.removeItem("eb_admin");
        } catch (e) {}
        </script>
        """,
        height=0,
        scrolling=False,
    )
