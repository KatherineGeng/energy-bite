"""User profile — nickname, gender, age group."""

from __future__ import annotations

import streamlit as st

from src.client_profile import bind_profile, decode_profile, profile_token, sync_profile_from_url
from src.constants import AGE_GROUP_OPTIONS, GENDER_OPTIONS
from src.database import save_user_profile


def profile_complete() -> bool:
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


def _inject_profile_storage_script(token: str) -> None:
    st.markdown(
        f"""
        <script>
        try {{
            localStorage.setItem("eb_profile", "{token}");
        }} catch (e) {{}}
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_onboarding() -> bool:
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
        _inject_profile_storage_script(token)
        st.rerun()
    return False
