"""Paste share-code import form + imported menu list."""

from __future__ import annotations

import streamlit as st

from src.database import append_menu_from_share, get_menu_row
from src.menu_persistence import load_user_menu_archive
from src.share_code import ShareCodeError, decode_share_code


def load_imported_menu_rows() -> list[dict[str, str]]:
    archive = load_user_menu_archive()
    if archive.empty:
        return []
    if "source" not in archive.columns:
        return []
    imported = archive[archive["source"].astype(str) == "import"].copy()
    if imported.empty:
        return []
    imported = imported.sort_values("saved_at", ascending=False)
    return [dict(row) for _, row in imported.iterrows()]


def render_import_share_form(*, key_prefix: str = "import") -> None:
    st.caption("粘贴朋友分享的简愈口令，一键存入私人菜单库。")
    pasted = st.text_area(
        "粘贴分享口令",
        placeholder="￥MENU:ING_001|ING_002:快速供能·肠脑舒缓:0.85￥",
        height=88,
        key=f"{key_prefix}_share_code",
    )
    import_name = st.text_input(
        "自定义菜单名称（可选）",
        placeholder="留空则自动生成",
        key=f"{key_prefix}_menu_name",
    )
    if st.button("确认导入", type="primary", use_container_width=True, key=f"{key_prefix}_submit"):
        try:
            payload = decode_share_code(pasted)
            new_id = append_menu_from_share(
                ingredient_ids=payload.ingredient_ids,
                energy_tags=payload.energy_tags,
                menu_name=import_name.strip(),
                description=f"由极客口令导入 · 预估分数 {payload.estimated_score:.2f}",
            )
            menu_row = get_menu_row(new_id, {})
            if menu_row:
                st.success(f"已导入 · {menu_row['menu_name']}（{new_id}）")
                st.rerun()
        except ShareCodeError as exc:
            st.error(str(exc))
        except ValueError as exc:
            st.error(str(exc))


def render_imported_menus_list(*, key_prefix: str = "import") -> None:
    rows = load_imported_menu_rows()
    if not rows:
        st.caption("暂无导入菜单 · 可在「分享」页粘贴口令导入")
        return

    keyword = st.text_input(
        "搜索导入菜单",
        placeholder="输入菜名、标签或关键词",
        key=f"{key_prefix}_search",
    )
    q = keyword.strip().lower()
    shown = 0
    for row in rows:
        name = str(row.get("menu_name", ""))
        tags = str(row.get("energy_tags", ""))
        meal = str(row.get("meal_type", ""))
        saved = str(row.get("saved_at", ""))[:10]
        haystack = f"{name} {tags} {meal} {row.get('menu_id', '')}".lower()
        if q and q not in haystack:
            continue
        shown += 1
        st.markdown(f"**{name}** · {meal}")
        st.caption(f"{tags.replace('·', ' · ')} · 导入于 {saved or '—'}")

    if q and shown == 0:
        st.info("未找到匹配的导入菜单。")
