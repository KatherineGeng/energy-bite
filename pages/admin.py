"""Admin backend — users, menus, image library."""

from __future__ import annotations

import streamlit as st

from src.calendar_utils import display_version
from src.constants import APP_VERSION
from src.database import (
    ASSETS_GALLERY_DIR,
    delete_app_image,
    get_app_image_bytes,
    init_database,
    list_app_images,
    load_all_user_profiles,
    load_ingredients,
    load_menus,
    save_app_image,
)
from src.profile_bootstrap import (
    admin_remember_token,
    clear_admin_from_browser,
    persist_admin_to_browser,
    restore_admin_from_browser,
)
from src.query_nav import qp_first


def _check_admin() -> bool:
    try:
        pwd = st.secrets.get("ADMIN_PASSWORD", "")
    except Exception:
        pwd = ""
    if not pwd:
        st.warning("未配置 ADMIN_PASSWORD，请在 Streamlit Secrets 中设置。")
        return False

    remember = admin_remember_token(str(pwd))
    if qp_first("adm") == remember:
        st.session_state.admin_authed = True

    restore_admin_from_browser()

    if st.session_state.get("admin_authed"):
        return True
    entered = st.text_input("管理员密码", type="password", key="admin_pwd_input")
    if st.button("登录", type="primary", key="admin_login"):
        if entered == pwd:
            st.session_state.admin_authed = True
            persist_admin_to_browser(remember)
            st.rerun()
        else:
            st.error("密码错误")
    return False


def _render_admin_header() -> None:
    st.markdown(
        f"**简愈管理后台** · 版本 **{display_version(APP_VERSION)}**  "
        f"（与用户 App 同一 Streamlit 部署，非独立站点）"
    )
    st.caption(
        "入口：`?nav=admin` · 题头版本号与用户端一致 · "
        "push GitHub 后 Streamlit Cloud 重新部署即同时更新用户页与管理页。"
    )


def _render_users_tab() -> None:
    df = load_all_user_profiles()
    if df.empty:
        st.info("暂无用户资料。")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("下载用户 CSV", csv, file_name="users.csv", mime="text/csv", key="admin_dl_users")


def _render_menus_tab() -> None:
    menus = load_menus()
    ingredients = load_ingredients()
    st.caption(f"共 {len(menus)} 道菜品 · {len(ingredients)} 种食材")
    if not menus.empty:
        st.dataframe(menus, use_container_width=True, hide_index=True)
        csv = menus.to_csv(index=False).encode("utf-8-sig")
        st.download_button("下载菜单 CSV", csv, file_name="menus.csv", mime="text/csv", key="admin_dl_menus")
    if not ingredients.empty:
        with st.expander("食材库"):
            st.dataframe(ingredients, use_container_width=True, hide_index=True)


def _image_grid(images: list[dict], *, deletable: bool) -> None:
    if not images:
        st.info("暂无图片。")
        return
    cols = st.columns(3)
    for i, row in enumerate(images):
        img_id = str(row["image_id"])
        with cols[i % 3]:
            data = get_app_image_bytes(img_id)
            if data:
                st.image(data, use_container_width=True)
            source = str(row.get("source", ""))
            title = str(row.get("title", img_id))
            st.caption(f"{title} · {source}")
            if deletable and st.button("删除", key=f"del_img_{img_id}"):
                delete_app_image(img_id)
                st.rerun()


def _render_images_tab() -> None:
    all_images = list_app_images()
    static_images = [r for r in all_images if str(r.get("source")) == "static"]
    user_images = [r for r in all_images if str(r.get("source")) == "user"]
    admin_images = [r for r in all_images if str(r.get("source")) == "admin"]

    st.markdown("#### 图片库存储说明")
    st.info(
        "**永久图库（推荐）**：文件放在 `assets/app_gallery/`，提交 GitHub 后全员可见，重新部署也不会丢失。\n\n"
        "**运行期图库**：用户在「分享 → 生成海报」上传的照片，或下方管理员临时导入，"
        "写入服务器 `data/app_images.csv`；Streamlit Cloud 重新部署后可能清空，"
        "重要图片请复制到 `assets/app_gallery/` 再 push。"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("永久图库", len(static_images))
    c2.metric("用户上传", len(user_images))
    c3.metric("管理员导入", len(admin_images))
    c4.metric("合计", len(all_images))

    gallery_path = ASSETS_GALLERY_DIR
    st.caption(f"永久图库目录：`{gallery_path}`（当前 {len(static_images)} 张）")

    sub_static, sub_runtime, sub_import = st.tabs(
        ["🌿 永久图库（Git）", "📷 用户上传", "⬆️ 管理员导入"]
    )

    with sub_static:
        st.caption("由仓库内 PNG/JPG 自动加载；新增图片请放入上述目录并 push，无需在此上传。")
        _image_grid(static_images, deletable=False)

    with sub_runtime:
        st.caption("用户在海报页上传餐食实拍时，会自动调用 save_uploads_to_library 写入运行期图库。")
        _image_grid(user_images, deletable=True)

    with sub_import:
        st.caption("临时追加到运行期图库；若需长期保留，请将文件放入 assets/app_gallery/ 并 push。")
        uploaded = st.file_uploader(
            "选择 PNG / JPG",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="admin_image_upload",
        )
        if uploaded and st.button("导入到运行期图库", type="primary", key="admin_import_btn"):
            for f in uploaded:
                save_app_image(f.getvalue(), source="admin", title=f.name)
            st.success(f"已导入 {len(uploaded)} 张图片")
            st.rerun()
        _image_grid(admin_images, deletable=True)


def render() -> None:
    init_database()

    if not _check_admin():
        return

    _render_admin_header()
    tab_u, tab_m, tab_i = st.tabs(["👤 用户信息", "🍽 菜单菜品", "🖼 图片库"])
    with tab_u:
        _render_users_tab()
    with tab_m:
        _render_menus_tab()
    with tab_i:
        _render_images_tab()

    if st.button("退出管理", key="admin_logout"):
        st.session_state.admin_authed = False
        clear_admin_from_browser()
        st.session_state.current_page = "morning"
        st.rerun()
