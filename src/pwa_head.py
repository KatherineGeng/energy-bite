"""Lightweight PWA / iOS icon tags (mobile-safe, no heavy JS)."""

from __future__ import annotations

import streamlit as st

from src.constants import APP_VERSION

_STATIC_ICON = f"/app/static/apple-touch-icon.png?v={APP_VERSION}"


def inject_pwa_head() -> None:
    """Minimal head tags — avoids iframe JS that can hang mobile Streamlit."""
    st.markdown(
        f"""
        <link rel="apple-touch-icon" href="{_STATIC_ICON}" sizes="180x180">
        <link rel="icon" href="{_STATIC_ICON}" sizes="32x32">
        <meta name="apple-mobile-web-app-title" content="简愈">
        <meta name="theme-color" content="#8DA399">
        """,
        unsafe_allow_html=True,
    )
