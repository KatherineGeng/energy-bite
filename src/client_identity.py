"""Identify returning visitors — IP on Cloud, session token locally."""

from __future__ import annotations

import uuid

import streamlit as st


def _detect_client_key() -> str:
    try:
        ip = getattr(st.context, "ip_address", None)
        if ip:
            return str(ip).strip()
    except Exception:
        pass

    try:
        headers = getattr(st.context, "headers", None) or {}
        forwarded = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
        if forwarded:
            return str(forwarded).split(",")[0].strip()
        real_ip = headers.get("X-Real-Ip") or headers.get("x-real-ip")
        if real_ip:
            return str(real_ip).strip()
    except Exception:
        pass

    if "eb_client_token" not in st.session_state:
        st.session_state.eb_client_token = uuid.uuid4().hex[:16]
    return f"session-{st.session_state.eb_client_token}"


def client_ip() -> str:
    """Stable per-browser key for profile lookup."""
    if st.session_state.get("eb_client_key"):
        return str(st.session_state.eb_client_key)
    key = _detect_client_key()
    st.session_state.eb_client_key = key
    return key


def bind_client_key(key: str) -> None:
    """Pin profile key for this session after onboarding."""
    st.session_state.eb_client_key = str(key).strip()
    st.session_state.eb_profile_done = True
