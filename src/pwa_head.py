"""Minimal iOS meta tags + client profile restore."""

from __future__ import annotations

import streamlit as st


def inject_pwa_head() -> None:
    st.markdown(
        """
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="theme-color" content="#8DA399">
        <script>
        (function () {
          try {
            var u = new URL(window.location.href);
            var ebp = u.searchParams.get("ebp");
            var stored = localStorage.getItem("eb_profile");
            if (ebp) {
              localStorage.setItem("eb_profile", ebp);
              return;
            }
            if (stored && !ebp) {
              u.searchParams.set("ebp", stored);
              window.location.replace(u.toString());
            }
          } catch (e) {}
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )
