"""App image library — user uploads + admin imports."""

from __future__ import annotations

import base64
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from src.database import get_app_image_bytes, list_app_images, save_app_image
from src.nav_params import append_nav_params

GALLERY_INITIAL_COUNT = 9


def _gallery_pick_href(image_id: str) -> str:
    page = st.session_state.get("current_page", "export")
    return append_nav_params(
        f"?nav={quote(page)}&export_tab=poster&gallery_pick={quote(image_id)}"
    )


def _mime_for_filename(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


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


def _render_gallery_grid(images: list[dict[str, str]], selected_ids: list[str]) -> None:
    cells: list[str] = []
    for row in images:
        img_id = str(row["image_id"])
        data = get_app_image_bytes(img_id)
        if not data:
            continue
        filename = str(row.get("filename") or f"{img_id}.jpg")
        mime = _mime_for_filename(filename)
        b64 = base64.b64encode(data).decode("ascii")
        picked = img_id in selected_ids
        btn_cls = "eb-gallery-pick-btn picked" if picked else "eb-gallery-pick-btn"
        label = "✓ 已选" if picked else "选择"
        href = _gallery_pick_href(img_id)
        cells.append(
            f'<div class="eb-gallery-cell">'
            f'<img class="eb-gallery-thumb" src="data:{mime};base64,{b64}" alt="" loading="lazy" />'
            f'<a class="{btn_cls}" href="{href}">{label}</a>'
            f"</div>"
        )
    if cells:
        st.markdown(f'<div class="eb-gallery-grid">{"".join(cells)}</div>', unsafe_allow_html=True)


def render_gallery_picker(key: str, *, max_select: int = 2) -> list[bytes]:
    """Collapsed gallery: expand on「查看」, pick via HTML links."""
    images = list_app_images()
    open_key = f"{key}_open"
    show_all_key = f"{key}_show_all"
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
                st.session_state[show_all_key] = False
                st.session_state.pop("poster_gallery_open", None)
                st.rerun()
        elif st.button("查看", key=f"{key}_open", use_container_width=True):
            st.session_state[open_key] = True
            st.rerun()

    if not st.session_state.get(open_key):
        return _selected_bytes(selected_ids)

    st.caption(f"点「选择」标记图片（最多 {max_select} 张，再次点击取消）")
    show_all = bool(st.session_state.get(show_all_key))
    visible = images if show_all else images[:GALLERY_INITIAL_COUNT]
    _render_gallery_grid(visible, selected_ids)

    remaining = len(images) - len(visible)
    if remaining > 0:
        if st.button(f"查看更多（还有 {remaining} 张）", key=f"{key}_more", use_container_width=True):
            st.session_state[show_all_key] = True
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
