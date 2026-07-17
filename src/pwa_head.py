"""Minimal iOS meta tags — Safari-safe. Icons cleared by parent-document JS in app.py."""

from __future__ import annotations

import streamlit as st


def inject_pwa_head() -> None:
    # Do not inject favicon / apple-touch-icon here: iOS ignores SVG touch icons,
    # and Streamlit's default red icon is removed via components.html in app.py.
    st.markdown(
        """
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="简愈一人食">
        <meta name="theme-color" content="#8DA399">
        """,
        unsafe_allow_html=True,
    )
