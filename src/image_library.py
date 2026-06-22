"""App image library — user uploads + admin imports."""

from __future__ import annotations

from urllib.parse import quote

import streamlit as st

from src.database import get_app_image_bytes, list_app_images, save_app_image
from src.nav_params import append_nav_params


def _gallery_pick_href(image_id: str) -> str:
    page = st.session_state.get("current_page", "export")
    return append_nav_params(
        f"?nav={quote(page)}&export_tab=poster&gallery_pick={quote(image_id)}"
    )


def apply_gallery_pick_action() -> None:
    """Toggle poster gallery selection from URL (mobile-safe)."""
    from src.query_nav import pop_query_param

    pick = pop_query_param("gallery_pick")
    if not pick:
        return
    key = "poster_gallery"
    selected = list(st.session_state.get(key, []))
    if pick in selected:
        selected = [x for x in selected if x != pick]
    elif len(selected) < 2:
        selected.append(pick)
    else:
        st.toast("最多选择 2 张")
    st.session_state[key] = selected
    st.session_state["poster_gallery_open"] = True
    st.rerun()


def render_gallery_picker(key: str, *, max_select: int = 2) -> list[bytes]:
    """Collapsed gallery: expand on「查看」, pick via HTML links."""
    images = list_app_images()
    open_key = f"{key}_open"
    selected_ids: list[str] = list(st.session_state.get(key, []))

    if not images:
        st.caption("图片库暂无图片。上传餐食照片后会自动收录。")
        return []

    if st.session_state.get("poster_gallery_open"):
        st.session_state[open_key] = True

    picked_n = len(selected_ids)
    hint = f"已选 {picked_n}/{max_select} 张" if picked_n else f"共 {len(images)} 张可选"

    head_col, action_col = st.columns([3, 1], gap="small")
    with head_col:
        st.caption(f"App 图片库 · {hint}")
    with action_col:
        if st.session_state.get(open_key):
            if st.button("收起", key=f"{key}_close", use_container_width=True):
                st.session_state[open_key] = False
                st.session_state.pop("poster_gallery_open", None)
                st.rerun()
        elif st.button("查看", key=f"{key}_open", use_container_width=True):
            st.session_state[open_key] = True
            st.rerun()

    if not st.session_state.get(open_key):
        return _selected_bytes(selected_ids)

    st.caption(f"点「选择」标记图片（最多 {max_select} 张，再次点击取消）")
    cols = st.columns(3)
    for i, row in enumerate(images):
        img_id = str(row["image_id"])
        with cols[i % 3]:
            data = get_app_image_bytes(img_id)
            if data:
                st.image(data, use_container_width=True)
            picked = img_id in selected_ids
            label = "✓ 已选" if picked else "选择"
            cls = "eb-gallery-pick-btn picked" if picked else "eb-gallery-pick-btn"
            href = _gallery_pick_href(img_id)
            st.markdown(
                f'<a class="{cls}" href="{href}">{label}</a>',
                unsafe_allow_html=True,
            )

    return _selected_bytes(selected_ids)


def _selected_bytes(selected_ids: list[str]) -> list[bytes]:
    out: list[bytes] = []
    for img_id in selected_ids:
        data = get_app_image_bytes(img_id)
        if data:
            out.append(data)
    return out


def save_uploads_to_library(uploads, *, source: str = "user") -> list[str]:
    """Persist uploaded files to library; return image_ids."""
    ids: list[str] = []
    for f in uploads or []:
        img_id = save_app_image(f.getvalue(), source=source, title=getattr(f, "name", "upload"))
        ids.append(img_id)
    return ids
