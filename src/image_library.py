"""App image library — user uploads + admin imports."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.database import get_app_image_bytes, list_app_images, save_app_image


def render_gallery_picker(key: str, *, max_select: int = 2) -> list[bytes]:
    """Show image library grid; return selected image bytes."""
    images = list_app_images()
    if not images:
        st.caption("图片库暂无图片。上传餐食照片后会自动收录。")
        return []

    st.caption(f"从 App 图片库选择（共 {len(images)} 张，可多选）")
    selected_ids: list[str] = st.session_state.get(key, [])
    cols = st.columns(3)
    for i, row in enumerate(images[:12]):
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
