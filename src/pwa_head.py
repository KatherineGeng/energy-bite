"""Minimal iOS meta tags — Safari-safe; favicon via inline Data URI SVG."""

from __future__ import annotations

import streamlit as st

# Same green「简」icon as app.py — no external image URL.
APP_ICON_DATA_URI = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' fill='%238DA399'/>"
    "<text x='50' y='50' font-family='sans-serif' font-size='60' font-weight='bold' "
    "fill='white' text-anchor='middle' dominant-baseline='central'>%E7%AE%80</text>"
    "</svg>"
)


def inject_pwa_head() -> None:
    st.markdown(
        f"""
        <link rel="icon" href="{APP_ICON_DATA_URI}" type="image/svg+xml">
        <link rel="shortcut icon" href="{APP_ICON_DATA_URI}" type="image/svg+xml">
        <link rel="apple-touch-icon" href="{APP_ICON_DATA_URI}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="theme-color" content="#8DA399">
        """,
        unsafe_allow_html=True,
    )
