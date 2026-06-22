"""Minimal iOS meta tags — no <link> in body (Safari-safe)."""

from __future__ import annotations

import streamlit as st


def inject_pwa_head() -> None:
    st.markdown(
        """
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="theme-color" content="#8DA399">
        """,
        unsafe_allow_html=True,
    )
