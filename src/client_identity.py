"""Identify returning visitors — IP on Cloud, session token locally."""

from __future__ import annotations

import uuid

import streamlit as st


def client_ip() -> str:
    """Best-effort client key for profile lookup."""
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
