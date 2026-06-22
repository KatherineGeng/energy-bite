"""Client-side profile token (ebp) — survives Streamlit Cloud redeploy."""

from __future__ import annotations

import base64
import json
from urllib.parse import quote

import streamlit as st

from src.query_nav import qp_first

_PROFILE_KEY = "eb_profile_ebp"


def encode_profile(nickname: str, gender: str, age_group: str) -> str:
    payload = json.dumps(
        {"n": nickname.strip(), "g": gender, "a": age_group},
        ensure_ascii=False,
    )
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_profile(token: str) -> dict[str, str] | None:
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        nick = str(data.get("n", "")).strip()
        if not nick:
            return None
        return {
            "nickname": nick,
            "gender": str(data.get("g", "")),
            "age_group": str(data.get("a", "")),
        }
    except Exception:
        return None


def sync_profile_from_url() -> None:
    """Load profile token from URL into session (keep param for full page reloads)."""
    ebp = qp_first("ebp")
    if ebp:
        profile = decode_profile(ebp)
        if profile:
            st.session_state[_PROFILE_KEY] = ebp
            st.session_state.eb_profile = profile


def profile_token() -> str:
    return str(st.session_state.get(_PROFILE_KEY, "") or qp_first("ebp") or "")


def profile_query_suffix() -> str:
    token = profile_token()
    return f"&ebp={quote(token)}" if token else ""


def bind_profile(nickname: str, gender: str, age_group: str) -> str:
    token = encode_profile(nickname, gender, age_group)
    st.session_state[_PROFILE_KEY] = token
    st.session_state.eb_profile = {
        "nickname": nickname.strip(),
        "gender": gender,
        "age_group": age_group,
    }
    st.query_params["ebp"] = token
    return token
