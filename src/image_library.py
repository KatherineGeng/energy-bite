"""App image library — user uploads + admin imports."""

from __future__ import annotations

import streamlit as st

from src.database import get_app_image_bytes, list_app_images, save_app_image


def render_gallery_picker(key: str, *, max_select: int = 2) -> list[bytes]:
    """Collapsed gallery: expand on「查看」, then pick images for poster."""
    images = list_app_images()
    open_key = f"{key}_open"
    selected_ids: list[str] = list(st.session_state.get(key, []))

    if not images:
        st.caption("图片库暂无图片。上传餐食照片后会自动收录。")
        return []

    picked_n = len(selected_ids)
    if picked_n:
        hint = f"已选 {picked_n}/{max_select} 张"
    else:
        hint = f"共 {len(images)} 张可选"

    head_col, action_col = st.columns([3, 1], gap="small")
    with head_col:
        st.caption(f"App 图片库 · {hint}")
    with action_col:
        if st.session_state.get(open_key):
            if st.button("收起", key=f"{key}_close", use_container_width=True):
                st.session_state[open_key] = False
                st.rerun()
        else:
            if st.button("查看", key=f"{key}_open", use_container_width=True):
                st.session_state[open_key] = True
                st.rerun()

    if not st.session_state.get(open_key):
        return _selected_bytes(selected_ids)

    st.caption(f"点选最多 {max_select} 张（再次点击取消选择）")
    cols = st.columns(3)
    for i, row in enumerate(images):
        img_id = str(row["image_id"])
        with cols[i % 3]:
            data = get_app_image_bytes(img_id)
            if data:
                st.image(data, use_container_width=True)
            picked = img_id in selected_ids
            label = "✓ 已选" if picked else "选择"
            if st.button(label, key=f"{key}_{img_id}", use_container_width=True):
                if picked:
                    selected_ids = [x for x in selected_ids if x != img_id]
                elif len(selected_ids) < max_select:
                    selected_ids = selected_ids + [img_id]
                else:
                    st.toast(f"最多选择 {max_select} 张")
                st.session_state[key] = selected_ids
                st.rerun()

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
