"""Append stable query params to HTML navigation links."""

from __future__ import annotations

from urllib.parse import quote

import streamlit as st

from src.client_profile import profile_query_suffix


def append_nav_params(href: str) -> str:
    suffix = profile_query_suffix()
    if not suffix:
        return href
    return href + suffix
