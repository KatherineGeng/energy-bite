"""User profile — nickname, gender, age group; Supabase auth when configured."""

from __future__ import annotations

import streamlit as st

from src.client_profile import bind_profile, decode_profile, profile_token, sync_profile_from_url
from src.constants import AGE_GROUP_OPTIONS, GENDER_OPTIONS
from src.database import save_user_profile
from src.db_config import postgres_enabled
from src.profile_bootstrap import persist_profile_to_browser


def profile_complete() -> bool:
    if postgres_enabled():
        from src.db_auth import current_user_id, restore_session_user

        return bool(current_user_id()) and restore_session_user()

    sync_profile_from_url()
    token = profile_token()
    if not token:
        return False
    profile = st.session_state.get("eb_profile") or decode_profile(token)
    if profile and str(profile.get("nickname", "")).strip():
        st.session_state.eb_profile = profile
        return True
    return False


def nickname() -> str:
    if postgres_enabled():
        from src.db_auth import current_profile

        profile = current_profile()
        if profile:
            return str(profile.get("nickname", "")).strip()
        return ""

    sync_profile_from_url()
    profile = st.session_state.get("eb_profile")
    if profile:
        return str(profile.get("nickname", "")).strip()
    token = profile_token()
    if token:
        decoded = decode_profile(token)
        if decoded:
            return str(decoded.get("nickname", "")).strip()
    return ""


def morning_greeting() -> str:
    name = nickname()
    if name:
        return f"{name}，早上好～新的一天开始了"
    return "早上好～新的一天开始了"


def planning_prompt() -> str:
    name = nickname()
    if name:
        return f"开始规划餐食，{name}今天想吃什么？"
    return "开始规划餐食，今天想吃什么？"


def _render_pg_auth() -> bool:
    from src.db_auth import login_user, register_user

    st.markdown("### 欢迎使用简愈一人食")
    st.caption("昵称 + 4 位 PIN 登录，手机与电脑数据同步。")

    tab_login, tab_register = st.tabs(["登录", "新用户注册"])

    with tab_login:
        nick = st.text_input("昵称", key="pg_login_nick", placeholder="例如：小愈")
        pin = st.text_input("PIN（4 位数字）", type="password", max_chars=4, key="pg_login_pin")
        if st.button("登录", type="primary", use_container_width=True, key="pg_login_btn"):
            try:
                login_user(nick, pin.strip())
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))

    with tab_register:
        nick = st.text_input("昵称", key="pg_reg_nick", placeholder="例如：小愈")
        gender = st.selectbox("性别", GENDER_OPTIONS, key="pg_reg_gender")
        age_group = st.selectbox("年龄段", AGE_GROUP_OPTIONS, key="pg_reg_age")
        pin = st.text_input("设置 PIN（4 位数字）", type="password", max_chars=4, key="pg_reg_pin")
        pin2 = st.text_input("确认 PIN", type="password", max_chars=4, key="pg_reg_pin2")
        if st.button("注册并开始", type="primary", use_container_width=True, key="pg_reg_btn"):
            if pin.strip() != pin2.strip():
                st.warning("两次 PIN 不一致。")
                return False
            try:
                register_user(nick, gender, age_group, pin.strip())
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))

    return False


def render_onboarding() -> bool:
    if postgres_enabled():
        return _render_pg_auth()

    st.markdown("### 欢迎使用简愈一人食")
    st.caption("请填写基本信息，我们会记住您的昵称。")

    nick = st.text_input("昵称", placeholder="例如：小愈", key="onboard_nickname")
    gender = st.selectbox("性别", GENDER_OPTIONS, key="onboard_gender")
    age_group = st.selectbox("年龄段", AGE_GROUP_OPTIONS, key="onboard_age")

    if st.button("开始使用", type="primary", use_container_width=True, key="onboard_save"):
        text = nick.strip()
        if not text:
            st.warning("请填写昵称。")
            return False
        token = bind_profile(text, gender, age_group)
        save_user_profile(text, gender, age_group, client_ip="local")
        persist_profile_to_browser(token)
        st.rerun()
    return False
