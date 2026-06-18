"""Morning workbench — Energy Bite 4.0."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.database import get_ingredient_map, get_menu_by_id, init_database, load_menus
from src.nutrition import coverage_summary
from src.recommendation import format_ingredient_names, get_daily_menus
from src.theme import page_title, section_title


def _sync_draft(menu_ids: list[str]) -> None:
    st.session_state.current_day_menus = menu_ids
    st.session_state.today_recommendations = menu_ids


def _store_recommendations(recs) -> None:
    ids = recs["menu_id"].tolist() if not recs.empty else []
    _sync_draft(ids)
    st.session_state.today_menus = recs.to_dict("records") if not recs.empty else []
    st.session_state.menu_locked = False
    st.session_state.final_daily_list = []


def _get_morning_inputs() -> dict:
    return st.session_state.get(
        "morning_inputs",
        {
            "sleep": st.session_state.get("morning_sleep", "良好"),
            "load": st.session_state.get("morning_load", "中等"),
            "meal_count": st.session_state.get("morning_meal_count", 3),
        },
    )


def _remove_menu(menu_id: str) -> None:
    ids = [mid for mid in st.session_state.current_day_menus if mid != menu_id]
    _sync_draft(ids)
    st.session_state.menu_locked = False
    st.session_state.final_daily_list = []


def _add_menu(menu_id: str) -> None:
    if menu_id and menu_id not in st.session_state.current_day_menus:
        _sync_draft(st.session_state.current_day_menus + [menu_id])
        st.session_state.menu_locked = False
        st.session_state.final_daily_list = []


def render() -> None:
    init_database()
    all_menus = load_menus()

    page_title("fa-sun", "晨间餐饮", "规划今日一人食，确认后进入晚间回顾。")

    locked = st.session_state.get("menu_locked", False)
    if locked and st.session_state.get("final_daily_list"):
        st.success("今日就餐计划已确认 · 可前往「晚间回顾」。")

    sleep = st.selectbox("昨晚睡眠状态", ["很好", "良好", "一般", "较差"], key="morning_sleep")
    load = st.selectbox("今日脑力/体力消耗", ["低", "中等", "高"], index=1, key="morning_load")
    meal_count = st.selectbox("今日一人食餐数", [1, 2, 3], index=2, key="morning_meal_count")

    col1, col2 = st.columns(2, gap="small")
    with col1:
        if st.button("生成菜单", type="primary", use_container_width=True, key="gen_menus", disabled=locked):
            recs = get_daily_menus(sleep, load, int(meal_count))
            st.session_state.morning_inputs = {"sleep": sleep, "load": load, "meal_count": int(meal_count)}
            _store_recommendations(recs)
            st.session_state.today_date = date.today().isoformat()
            st.rerun()
    with col2:
        if st.button("换一套", use_container_width=True, key="shuffle_menus", disabled=locked):
            morning = _get_morning_inputs()
            current = st.session_state.get("current_day_menus", [])
            new_recs = get_daily_menus(
                morning.get("sleep", sleep),
                morning.get("load", load),
                int(morning.get("meal_count", meal_count)),
                shuffle=True,
                exclude_menu_ids=current if current else None,
            )
            _store_recommendations(new_recs)
            st.rerun()

    menu_ids: list[str] = list(st.session_state.get("current_day_menus", []))
    if not menu_ids:
        st.info("点击「生成菜单」或「换一套」，开始规划今日一人食。")
        return

    section_title("fa-clipboard-list", "今日菜单")

    ingredient_map = get_ingredient_map()
    display_ids = st.session_state.get("final_daily_list") if locked else menu_ids

    for menu_id in display_ids:
        row = get_menu_by_id(menu_id)
        if not row:
            continue
        tags_str = row.get("energy_tags", "").replace("·", " · ")
        ingredients = format_ingredient_names(row, ingredient_map)
        coverage = coverage_summary(row)

        with st.container(border=True):
            if locked:
                st.markdown(f"**{row['menu_name']}**")
                st.caption(f"{row['meal_type']} · {tags_str} · 营养覆盖 {coverage}")
                st.write(f"食材：{ingredients}")
            else:
                info_col, action_col = st.columns([5, 1])
                with info_col:
                    st.markdown(f"**{row['menu_name']}**")
                    st.caption(
                        f"{row['meal_type']} · {tags_str} · ⏱ {row['prep_minutes']} min · 营养覆盖 {coverage}"
                    )
                    st.write(f"食材：{ingredients}")
                with action_col:
                    if st.button(f"移除", key=f"remove_{menu_id}", use_container_width=True):
                        _remove_menu(menu_id)
                        st.rerun()

    if not locked:
        available = all_menus[~all_menus["menu_id"].isin(menu_ids)] if not all_menus.empty else all_menus
        if not available.empty:
            add_col, btn_col = st.columns([3, 1])
            with add_col:
                add_options = available["menu_id"].tolist()
                add_labels = {
                    r["menu_id"]: f"{r['menu_name']}（{r['meal_type']}）"
                    for _, r in available.iterrows()
                }
                pick = st.selectbox(
                    "从菜单库添加",
                    add_options,
                    format_func=lambda x: add_labels.get(x, x),
                    key="add_menu_pick",
                    label_visibility="collapsed",
                )
            with btn_col:
                if st.button("加入", use_container_width=True, key="add_menu_btn"):
                    _add_menu(pick)
                    st.rerun()

        if st.button("确认今日就餐计划", type="primary", use_container_width=True, key="confirm_plan"):
            st.session_state.final_daily_list = list(menu_ids)
            st.session_state.menu_locked = True
            st.rerun()
