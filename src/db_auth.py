"""User authentication — nickname + 4-digit PIN (Supabase)."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

import streamlit as st

from src.db_connection import pg_cursor
from src.query_nav import qp_first

_SESSION_USER_ID = "eb_user_id"
_SESSION_PROFILE = "eb_profile"
_QUERY_USER_KEY = "u"


def _hash_pin(pin: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def _verify_pin(pin: str, stored: str) -> bool:
    try:
        salt, _hex = stored.split("$", 1)
    except ValueError:
        return False
    check = _hash_pin(pin, salt)
    return secrets.compare_digest(check, stored)


def _profile_from_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "user_id": str(row["id"]),
        "nickname": str(row["nickname"]),
        "gender": str(row.get("gender") or ""),
        "age_group": str(row.get("age_group") or ""),
    }


def register_user(nickname: str, gender: str, age_group: str, pin: str) -> dict[str, str]:
    nick = nickname.strip()
    if not nick:
        raise ValueError("昵称不能为空")
    if not pin.isdigit() or len(pin) != 4:
        raise ValueError("PIN 须为 4 位数字")
    pin_hash = _hash_pin(pin)
    with pg_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE nickname = %s", (nick,))
        if cur.fetchone():
            raise ValueError("该昵称已注册，请直接登录")
        cur.execute(
            """
            INSERT INTO users (nickname, pin_hash, gender, age_group)
            VALUES (%s, %s, %s, %s)
            RETURNING id, nickname, gender, age_group
            """,
            (nick, pin_hash, gender, age_group),
        )
        row = cur.fetchone()
    profile = _profile_from_row(row)
    _bind_session(profile)
    return profile


def login_user(nickname: str, pin: str) -> dict[str, str]:
    nick = nickname.strip()
    if not nick:
        raise ValueError("请填写昵称")
    if not pin.isdigit() or len(pin) != 4:
        raise ValueError("PIN 须为 4 位数字")
    with pg_cursor() as cur:
        cur.execute(
            "SELECT id, nickname, gender, age_group, pin_hash FROM users WHERE nickname = %s",
            (nick,),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError("昵称不存在，请先注册")
    if not _verify_pin(pin, str(row["pin_hash"])):
        raise ValueError("PIN 错误")
    profile = _profile_from_row(row)
    _bind_session(profile)
    return profile


def _bind_session(profile: dict[str, str]) -> None:
    st.session_state[_SESSION_USER_ID] = profile["user_id"]
    st.session_state[_SESSION_PROFILE] = profile
    for key in ("ebp", "eb_profile_ebp"):
        st.session_state.pop(key, None)
    try:
        if "ebp" in st.query_params:
            del st.query_params["ebp"]
        st.query_params[_QUERY_USER_KEY] = profile["user_id"]
    except Exception:
        pass


def restore_session_user() -> bool:
    uid = st.session_state.get(_SESSION_USER_ID) or qp_first(_QUERY_USER_KEY)
    if not uid:
        return False
    st.session_state[_SESSION_USER_ID] = str(uid)
    profile = st.session_state.get(_SESSION_PROFILE)
    if profile and str(profile.get("user_id")) == str(uid):
        return True
    with pg_cursor() as cur:
        cur.execute(
            "SELECT id, nickname, gender, age_group FROM users WHERE id = %s::uuid",
            (str(uid),),
        )
        row = cur.fetchone()
    if not row:
        logout_user()
        return False
    st.session_state[_SESSION_PROFILE] = _profile_from_row(row)
    return True


def auth_query_suffix() -> str:
    """Keep user id on HTML links (mobile full-page navigation)."""
    from urllib.parse import quote

    uid = current_user_id() or qp_first(_QUERY_USER_KEY) or ""
    return f"&{_QUERY_USER_KEY}={quote(str(uid))}" if uid else ""


def current_user_id() -> str:
    return str(st.session_state.get(_SESSION_USER_ID, "") or "")


def current_profile() -> dict[str, str] | None:
    if not current_user_id():
        return None
    return st.session_state.get(_SESSION_PROFILE)


def logout_user() -> None:
    st.session_state.pop(_SESSION_USER_ID, None)
    st.session_state.pop(_SESSION_PROFILE, None)
    try:
        if _QUERY_USER_KEY in st.query_params:
            del st.query_params[_QUERY_USER_KEY]
    except Exception:
        pass


def nickname_exists(nickname: str) -> bool:
    nick = nickname.strip()
    if not nick:
        return False
    with pg_cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE nickname = %s", (nick,))
        return cur.fetchone() is not None
