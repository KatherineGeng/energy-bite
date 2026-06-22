"""User profile — nickname, gender, age group."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.constants import AGE_GROUP_OPTIONS, GENDER_OPTIONS
from src.database import load_user_profile, save_user_profile


def profile_complete() -> bool:
    row = load_user_profile()
    return bool(row and str(row.get("nickname", "")).strip())


def nickname() -> str:
    row = load_user_profile()
    if row:
        return str(row.get("nickname", "")).strip()
    return ""


def morning_greeting() -> str:
    name = nickname()
    if name:
        return f"{name}，早上好～新的一天开始了"
    return "早上好～新的一天开始了"


def render_onboarding() -> bool:
    """Return True when profile saved and app may continue."""
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
        save_user_profile(text, gender, age_group)
        st.session_state.user_profile_loaded = True
        st.rerun()
    return False
