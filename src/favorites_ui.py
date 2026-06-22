"""Favorites list UI — collapsible sections with search."""

from __future__ import annotations

import streamlit as st

from src.database import load_favorites_dishes, load_favorites_menus, load_menus
from src.theme import TEXT


def _fav_matches_keyword(haystack: str, keyword: str) -> bool:
    q = keyword.strip()
    if not q:
        return True
    return q.lower() in haystack.lower()


def render_fav_menus_list(*, key_prefix: str = "fav") -> None:
    menus = load_favorites_menus()
    all_menus = load_menus()
    name_map = {r["menu_id"]: r["menu_name"] for _, r in all_menus.iterrows()} if not all_menus.empty else {}

    if menus.empty:
        st.caption("暂无收藏组合 · 可在「菜单」页点击「收藏此菜单」")
        return

    keyword = st.text_input(
        "搜索全天菜单",
        placeholder="输入菜名、日期或关键词",
        key=f"{key_prefix}_menus_search",
    )

    shown = 0
    for _, row in menus.iterrows():
        ids = [x for x in str(row["menu_ids"]).split("|") if x]
        names = " · ".join(name_map.get(mid, mid) for mid in ids)
        haystack = f"{row['date']} {names} {' '.join(ids)}"
        if not _fav_matches_keyword(haystack, keyword):
            continue
        shown += 1
        st.markdown(
            f'<div class="eb-fav-item"><strong>{row["date"]}</strong><br>'
            f'<span style="color:{TEXT};opacity:0.78;font-size:0.88rem;">{names}</span></div>',
            unsafe_allow_html=True,
        )

    if keyword.strip() and shown == 0:
        st.info("未找到匹配的收藏菜单。")


def render_fav_dishes_list(*, key_prefix: str = "fav") -> None:
    dishes = load_favorites_dishes()
    all_menus = load_menus()
    name_map = {r["menu_id"]: r["menu_name"] for _, r in all_menus.iterrows()} if not all_menus.empty else {}

    if dishes.empty:
        st.caption("暂无收藏菜品 · 可在「回顾」页收藏单道菜")
        return

    keyword = st.text_input(
        "搜索单个菜品",
        placeholder="输入菜名、日期或关键词",
        key=f"{key_prefix}_dishes_search",
    )

    shown = 0
    for _, row in dishes.iterrows():
        name = name_map.get(row["menu_id"], row["menu_id"])
        haystack = f"{name} {row['menu_id']} {row['date']}"
        if not _fav_matches_keyword(haystack, keyword):
            continue
        shown += 1
        st.write(f"· {name}（{row['date']}）")

    if keyword.strip() and shown == 0:
        st.info("未找到匹配的收藏菜品。")


def render_collapsible_favorites(*, key_prefix: str = "mine") -> None:
    """Two toggle buttons; content expands only after click."""
    if f"{key_prefix}_fav_open" not in st.session_state:
        st.session_state[f"{key_prefix}_fav_open"] = None

    open_section = st.session_state[f"{key_prefix}_fav_open"]
    col_a, col_b = st.columns(2, gap="small")
    with col_a:
        if st.button(
            "🌟 全天菜单",
            key=f"{key_prefix}_btn_menus",
            use_container_width=True,
            type="primary" if open_section == "menus" else "secondary",
        ):
            st.session_state[f"{key_prefix}_fav_open"] = None if open_section == "menus" else "menus"
            st.rerun()
    with col_b:
        if st.button(
            "❤️ 单个菜品",
            key=f"{key_prefix}_btn_dishes",
            use_container_width=True,
            type="primary" if open_section == "dishes" else "secondary",
        ):
            st.session_state[f"{key_prefix}_fav_open"] = None if open_section == "dishes" else "dishes"
            st.rerun()

    if open_section == "menus":
        st.markdown('<div class="eb-mine-panel">', unsafe_allow_html=True)
        render_fav_menus_list(key_prefix=f"{key_prefix}_menus")
        st.markdown("</div>", unsafe_allow_html=True)
    elif open_section == "dishes":
        st.markdown('<div class="eb-mine-panel">', unsafe_allow_html=True)
        render_fav_dishes_list(key_prefix=f"{key_prefix}_dishes")
        st.markdown("</div>", unsafe_allow_html=True)
