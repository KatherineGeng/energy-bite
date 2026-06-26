"""Paste share-code import form + imported menu list."""

from __future__ import annotations

import streamlit as st

from src.database import append_menu_from_share, get_menu_row, load_ingredients
from src.menu_persistence import load_user_menu_archive
from src.share_code import ShareCodeError, decode_share_code, parse_share_paste_entries

_IMPORTED_ROWS_CACHE_KEY = "_imported_menu_rows_cache"


def invalidate_imported_menu_cache() -> None:
    st.session_state.pop(_IMPORTED_ROWS_CACHE_KEY, None)
    st.session_state.pop("_eb_ing_name_map", None)


def load_imported_menu_rows() -> list[dict[str, str]]:
    cached = st.session_state.get(_IMPORTED_ROWS_CACHE_KEY)
    if isinstance(cached, list):
        return cached

    archive = load_user_menu_archive()
    if archive.empty:
        st.session_state[_IMPORTED_ROWS_CACHE_KEY] = []
        return []
    if "source" not in archive.columns:
        st.session_state[_IMPORTED_ROWS_CACHE_KEY] = []
        return []
    imported = archive[archive["source"].astype(str) == "import"].copy()
    if imported.empty:
        st.session_state[_IMPORTED_ROWS_CACHE_KEY] = []
        return []
    imported = imported.sort_values("saved_at", ascending=False)
    rows = [dict(row) for _, row in imported.iterrows()]
    st.session_state[_IMPORTED_ROWS_CACHE_KEY] = rows
    return rows


def _ingredient_name_map() -> dict[str, str]:
    cached = st.session_state.get("_eb_ing_name_map")
    if isinstance(cached, dict):
        return cached
    df = load_ingredients()
    name_map = {str(r["id"]): str(r["name"]) for _, r in df.iterrows()} if not df.empty else {}
    st.session_state["_eb_ing_name_map"] = name_map
    return name_map


def _clean_tags(tags: str) -> str:
    text = str(tags or "").strip()
    if not text or "￥MENU:" in text or "\n" in text:
        return ""
    return text.replace("·", " · ")


def import_menus_from_share_text(pasted: str, *, default_name: str = "") -> list[str]:
    """Import one or many dishes from pasted share text."""
    entries = parse_share_paste_entries(pasted)
    if not entries:
        payload = decode_share_code(pasted)
        name = default_name.strip() or (
            f"{payload.energy_tags.split('·')[0]}组合" if payload.energy_tags else "好友分享菜单"
        )
        return [
            append_menu_from_share(
                ingredient_ids=payload.ingredient_ids,
                energy_tags=payload.energy_tags,
                menu_name=name,
                description=f"由极客口令导入 · 预估分数 {payload.estimated_score:.2f}",
            )
        ]

    menu_ids: list[str] = []
    for idx, entry in enumerate(entries, start=1):
        payload = decode_share_code(entry.code)
        if entry.menu_name:
            name = entry.menu_name
        elif default_name.strip() and len(entries) == 1:
            name = default_name.strip()
        else:
            tags = payload.energy_tags.split("·")
            name = f"{tags[0]}组合" if tags and tags[0] else f"导入菜单{idx}"
        menu_ids.append(
            append_menu_from_share(
                ingredient_ids=payload.ingredient_ids,
                energy_tags=payload.energy_tags,
                menu_name=name,
                meal_type=entry.meal_type,
                description=f"由极客口令导入 · 预估分数 {payload.estimated_score:.2f}",
            )
        )
    return menu_ids


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
        placeholder="留空则自动生成；粘贴全日口令时会按每道菜名称导入",
        key=f"{key_prefix}_menu_name",
    )
    if st.button("确认导入", type="primary", use_container_width=True, key=f"{key_prefix}_submit"):
        try:
            menu_ids = import_menus_from_share_text(pasted, default_name=import_name.strip())
            names: list[str] = []
            for mid in menu_ids:
                menu_row = get_menu_row(mid, {})
                if menu_row:
                    names.append(str(menu_row["menu_name"]))
            if names:
                invalidate_imported_menu_cache()
                st.session_state.export_action_panel = "import"
                if len(names) == 1:
                    st.session_state.eb_flash_success = f"已导入「{names[0]}」· 可在「我的 → 导入菜单」查看"
                else:
                    joined = "、".join(names[:4])
                    extra = f" 等 {len(names)} 道" if len(names) > 4 else f" 共 {len(names)} 道"
                    st.session_state.eb_flash_success = f"已导入{extra}：{joined} · 可在「我的 → 导入菜单」查看"
                st.session_state.pop(f"{key_prefix}_share_code", None)
                st.session_state.pop(f"{key_prefix}_menu_name", None)
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
    name_map = _ingredient_name_map()
    q = keyword.strip().lower()
    shown = 0
    for row in rows:
        name = str(row.get("menu_name", "")).strip()
        tags = _clean_tags(str(row.get("energy_tags", "")))
        meal = str(row.get("meal_type", "")).strip()
        saved = str(row.get("saved_at", ""))[:10]
        ing_ids = [x for x in str(row.get("ingredient_ids", "")).split("|") if x]
        ing_names = [name_map.get(i, i) for i in ing_ids]
        ing_line = " · ".join(ing_names)
        haystack = f"{name} {tags} {meal} {ing_line} {row.get('menu_id', '')}".lower()
        if q and q not in haystack:
            continue
        shown += 1
        st.markdown(f"**{name}**")
        detail_parts: list[str] = []
        if ing_line:
            detail_parts.append(f"食材：{ing_line}")
        if tags:
            detail_parts.append(tags)
        if meal:
            detail_parts.append(meal)
        detail_parts.append(f"导入于 {saved or '—'}")
        st.caption(" · ".join(detail_parts))

    if q and shown == 0:
        st.info("未找到匹配的导入菜单。")
