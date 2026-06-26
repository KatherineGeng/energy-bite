"""Favorites list UI — collapsible sections with search."""

from __future__ import annotations

from urllib.parse import quote

import streamlit as st

from src.database import load_favorites_dishes, load_favorites_menus, load_menus
from src.import_menu_ui import render_imported_menus_list
from src.nav_params import append_nav_params
from src.theme import TEXT


def _fav_matches_keyword(haystack: str, keyword: str) -> bool:
    q = keyword.strip()
    if not q:
        return True
    return q.lower() in haystack.lower()


def _fav_nav_href(tab: str) -> str:
    page = st.session_state.get("current_page", "mine")
    return append_nav_params(f"?nav={quote(page)}&act={quote(f'fav_{tab}')}")


def render_fav_nav_row(open_section: str | None) -> None:
    """Three horizontal nav links (mobile-safe HTML flex row)."""
    items = [
        ("menus", "🌟", "全天菜单"),
        ("dishes", "❤️", "单个菜品"),
        ("import", "📥", "导入菜单"),
    ]
    parts: list[str] = []
    for tab, icon, label in items:
        cls = "eb-fav-nav-btn"
        if open_section == tab:
            cls += " primary"
        inner = f"<span>{icon}</span><span>{label}</span>"
        parts.append(f'<a class="{cls}" href="{_fav_nav_href(tab)}">{inner}</a>')
    st.markdown(f'<div class="eb-fav-nav-row">{"".join(parts)}</div>', unsafe_allow_html=True)


def apply_fav_query_actions(*, key_prefix: str = "mine") -> None:
    from src.query_nav import pop_query_param

    act = pop_query_param("act")
    if act not in ("fav_menus", "fav_dishes", "fav_import"):
        return
    tab = act.removeprefix("fav_")
    state_key = f"{key_prefix}_fav_open"
    current = st.session_state.get(state_key)
    st.session_state[state_key] = None if current == tab else tab


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
    """Three toggle tabs: full-day menus, single dishes, imported menus (view only)."""
    if f"{key_prefix}_fav_open" not in st.session_state:
        st.session_state[f"{key_prefix}_fav_open"] = None

    open_section = st.session_state[f"{key_prefix}_fav_open"]
    render_fav_nav_row(open_section)

    if open_section == "menus":
        st.markdown('<div class="eb-mine-panel">', unsafe_allow_html=True)
        render_fav_menus_list(key_prefix=f"{key_prefix}_menus")
        st.markdown("</div>", unsafe_allow_html=True)
    elif open_section == "dishes":
        st.markdown('<div class="eb-mine-panel">', unsafe_allow_html=True)
        render_fav_dishes_list(key_prefix=f"{key_prefix}_dishes")
        st.markdown("</div>", unsafe_allow_html=True)
    elif open_section == "import":
        st.markdown('<div class="eb-mine-panel">', unsafe_allow_html=True)
        render_imported_menus_list(key_prefix=f"{key_prefix}_import_list")
        st.markdown("</div>", unsafe_allow_html=True)
