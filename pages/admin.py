"""Admin backend — users, menus, image library."""

from __future__ import annotations

import streamlit as st

from src.database import (
    delete_app_image,
    get_app_image_bytes,
    init_database,
    list_app_images,
    load_all_user_profiles,
    load_ingredients,
    load_menus,
    save_app_image,
)
from src.theme import page_title


def _check_admin() -> bool:
    try:
        pwd = st.secrets.get("ADMIN_PASSWORD", "")
    except Exception:
        pwd = ""
    if not pwd:
        st.warning("未配置 ADMIN_PASSWORD，请在 Streamlit Secrets 中设置。")
        return False
    if st.session_state.get("admin_authed"):
        return True
    entered = st.text_input("管理员密码", type="password", key="admin_pwd_input")
    if st.button("登录", type="primary", key="admin_login"):
        if entered == pwd:
            st.session_state.admin_authed = True
            st.rerun()
        else:
            st.error("密码错误")
    return False


def _render_users_tab() -> None:
    df = load_all_user_profiles()
    if df.empty:
        st.info("暂无用户资料。")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_menus_tab() -> None:
    menus = load_menus()
    ingredients = load_ingredients()
    st.caption(f"共 {len(menus)} 道菜品 · {len(ingredients)} 种食材")
    if not menus.empty:
        st.dataframe(menus, use_container_width=True, hide_index=True)
    if not ingredients.empty:
        with st.expander("食材库"):
            st.dataframe(ingredients, use_container_width=True, hide_index=True)


def _render_images_tab() -> None:
    st.caption("客户上传与管理員导入的图片均保存在 App 图片库。")
    uploaded = st.file_uploader(
        "管理员导入图片",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="admin_image_upload",
    )
    if uploaded and st.button("导入到图片库", key="admin_import_images"):
        for f in uploaded:
            save_app_image(f.getvalue(), source="admin", title=f.name)
        st.success(f"已导入 {len(uploaded)} 张图片")
        st.rerun()

    images = list_app_images()
    if not images:
        st.info("图片库为空。")
        return

    cols = st.columns(3)
    for i, row in enumerate(images):
        with cols[i % 3]:
            data = get_app_image_bytes(str(row["image_id"]))
            if data:
                st.image(data, use_container_width=True)
            st.caption(f"{row['title']} · {row['source']}")
            if st.button("删除", key=f"del_img_{row['image_id']}"):
                delete_app_image(str(row["image_id"]))
                st.rerun()


def render() -> None:
    init_database()
    page_title("", "后台管理")

    if not _check_admin():
        return

    tab_u, tab_m, tab_i = st.tabs(["👤 用户信息", "🍽 菜单菜品", "🖼 图片库"])
    with tab_u:
        _render_users_tab()
    with tab_m:
        _render_menus_tab()
    with tab_i:
        _render_images_tab()

    if st.button("退出管理", key="admin_logout"):
        st.session_state.admin_authed = False
        st.session_state.current_page = "morning"
        st.rerun()
