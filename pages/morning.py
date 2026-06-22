"""Morning workbench — 简愈一人食."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.constants import LIBRARY_GEN_MAX
from src.ai_menu import suggest_daily_menus_api
from src.database import (
    append_manual_menu,
    get_ingredient_map,
    get_menu_by_id,
    get_menus_by_pick_frequency,
    init_database,
    load_morning_context,
    save_daily_meal_plan,
    save_favorite_menu_set,
    search_menus_by_keyword,
)
from src.meal_plan_utils import (
    MEAL_ORDER,
    active_meal_slots,
    empty_meal_plan,
    flatten_plan,
    plan_from_menu_ids,
)
from src.session_hydrate import hydrate_today_state
from src.llm_client import has_api_key
from src.coverage_widget import render_coverage_badge, render_meal_headline
from src.nutrition import coverage_summary, menu_row_from_analysis
from src.nutrition_api import analyze_ingredients, parse_nutrition_from_description
from src.query_nav import pop_query_param
from src.recommendation import format_ingredient_names, get_daily_menus
from src.theme import section_title


def _has_morning_context(today_iso: str) -> bool:
    if st.session_state.get("morning_context_loaded") == today_iso:
        return bool(st.session_state.get("morning_inputs"))
    return load_morning_context(today_iso) is not None


def _active_meal_slots(meal_count: int) -> list[str]:
    return active_meal_slots(meal_count)


def _empty_meal_plan() -> dict[str, list[str]]:
    return empty_meal_plan()


def _flatten_plan(plan: dict[str, list[str]]) -> list[str]:
    return flatten_plan(plan)


def _plan_from_menu_ids(menu_ids: list[str]) -> dict[str, list[str]]:
    return plan_from_menu_ids(menu_ids, get_menu_by_id)


def _persist_plan(plan: dict[str, list[str]], *, confirmed: bool) -> None:
    today = st.session_state.get("today_date", date.today().isoformat())
    save_daily_meal_plan(today, plan, confirmed=confirmed)


def _sync_draft_from_plan(plan: dict[str, list[str]]) -> None:
    menu_ids = _flatten_plan(plan)
    st.session_state.meal_plan = plan
    st.session_state.current_day_menus = menu_ids
    st.session_state.today_recommendations = menu_ids
    _persist_plan(plan, confirmed=False)


def _ensure_meal_plan() -> dict[str, list[str]]:
    if st.session_state.get("meal_plan") and _flatten_plan(st.session_state.meal_plan):
        return st.session_state.meal_plan

    locked = st.session_state.get("menu_locked", False)
    if locked and st.session_state.get("final_meal_plan"):
        fp = st.session_state.final_meal_plan
        if _flatten_plan(fp):
            st.session_state.meal_plan = dict(fp)
            return st.session_state.meal_plan

    ids = list(st.session_state.get("current_day_menus", []))
    plan = _plan_from_menu_ids(ids)
    st.session_state.meal_plan = plan
    return plan


def _store_recommendations(recs) -> None:
    plan = _empty_meal_plan()
    if not recs.empty:
        for _, row in recs.iterrows():
            slot = row.get("meal_type", "午餐")
            if slot not in plan:
                slot = "午餐"
            plan[slot].append(row["menu_id"])
    _sync_draft_from_plan(plan)
    st.session_state.today_menus = recs.to_dict("records") if not recs.empty else []
    st.session_state.menu_locked = False
    st.session_state.final_daily_list = []
    st.session_state.final_meal_plan = _empty_meal_plan()
    st.session_state.eb_add_ui = None


def _get_morning_inputs() -> dict:
    return st.session_state.get(
        "morning_inputs",
        {
            "sleep": st.session_state.get("morning_sleep", "良好"),
            "load": st.session_state.get("morning_load", "中等"),
            "meal_count": st.session_state.get("morning_meal_count", 3),
        },
    )


def _on_remove_dish(meal_type: str, menu_id: str) -> None:
    plan = dict(st.session_state.get("meal_plan") or _empty_meal_plan())
    plan[meal_type] = [mid for mid in plan.get(meal_type, []) if mid != menu_id]
    st.session_state.meal_plan = plan
    st.session_state.current_day_menus = _flatten_plan(plan)
    st.session_state.today_recommendations = st.session_state.current_day_menus
    st.session_state.menu_locked = False
    st.session_state.final_daily_list = []
    st.session_state.final_meal_plan = _empty_meal_plan()
    st.session_state.eb_add_ui = None
    _persist_plan(plan, confirmed=False)


def _on_open_manual(meal_type: str) -> None:
    st.session_state.eb_add_ui = {"type": "manual", "meal": meal_type, "step": "search"}


def _on_start_new_dish(meal_type: str) -> None:
    name = st.session_state.get(f"manual_search_{meal_type}", "").strip()
    if not name:
        return
    st.session_state.eb_add_ui = {
        "type": "manual",
        "meal": meal_type,
        "step": "create",
        "draft_name": name,
    }


def _on_back_manual_search(meal_type: str) -> None:
    st.session_state.eb_add_ui = {"type": "manual", "meal": meal_type, "step": "search"}


def _on_pick_existing(meal_type: str, menu_id: str) -> None:
    _add_to_slot(meal_type, menu_id)
    _close_add_panel()


def _on_open_library(meal_type: str) -> None:
    st.session_state.eb_add_ui = {"type": "library", "meal": meal_type}


def _add_to_slot(meal_type: str, menu_id: str) -> None:
    if not menu_id:
        return
    plan = _ensure_meal_plan()
    slot = plan.setdefault(meal_type, [])
    if menu_id not in slot:
        slot.append(menu_id)
    _sync_draft_from_plan(plan)
    st.session_state.menu_locked = False
    st.session_state.final_daily_list = []
    st.session_state.final_meal_plan = _empty_meal_plan()


def _close_add_panel() -> None:
    st.session_state.eb_add_ui = None


def _today_gen_count() -> int:
    today = date.today().isoformat()
    if st.session_state.get("menu_gen_date") != today:
        return 0
    return int(st.session_state.get("menu_gen_count", 0))


def _increment_gen_count() -> int:
    today = date.today().isoformat()
    if st.session_state.get("menu_gen_date") != today:
        st.session_state.menu_gen_date = today
        st.session_state.menu_gen_count = 0
    n = _today_gen_count() + 1
    st.session_state.menu_gen_count = n
    return n


def _library_gens_remaining() -> int:
    return max(0, LIBRARY_GEN_MAX - _today_gen_count())


def _fetch_daily_menus(
    sleep: str,
    load: str,
    meal_count: int,
    *,
    shuffle: bool = False,
) -> None:
    """First LIBRARY_GEN_MAX times from library; then DeepSeek menu generation."""
    gen_num = _increment_gen_count()
    exclude = list(st.session_state.get("current_day_menus", [])) if shuffle else None

    use_api = gen_num > LIBRARY_GEN_MAX and has_api_key()
    if use_api:
        recs, note, new_ids = suggest_daily_menus_api(
            sleep, load, int(meal_count), exclude, shuffle=shuffle
        )
        if recs is not None and not recs.empty:
            st.session_state.last_gen_source = "api"
            st.session_state.last_gen_note = note
            st.session_state.ai_fresh_menu_ids = new_ids
            _store_recommendations(recs)
            return
        st.session_state.ai_fresh_menu_ids = []
        st.session_state.last_gen_note = (note or "AI 生成失败") + " 已回退菜品库。"

    recs = get_daily_menus(
        sleep,
        load,
        int(meal_count),
        shuffle=shuffle,
        exclude_menu_ids=exclude,
    )
    st.session_state.last_gen_source = "library"
    left = max(0, LIBRARY_GEN_MAX - gen_num)
    if gen_num <= LIBRARY_GEN_MAX:
        st.session_state.last_gen_note = (
            f"菜品库推荐（今日第 {gen_num}/{LIBRARY_GEN_MAX} 次库内生成"
            + (f"，剩余 {left} 次" if left else "，下次将启用 AI 推荐") + "）"
        )
    else:
        st.session_state.last_gen_note = "API 不可用或失败，已使用菜品库。"
    _store_recommendations(recs)


def _run_generate(sleep: str, load: str, meal_count: int) -> None:
    st.session_state.morning_inputs = {"sleep": sleep, "load": load, "meal_count": int(meal_count)}
    _fetch_daily_menus(sleep, load, int(meal_count), shuffle=False)
    st.session_state.today_date = date.today().isoformat()


def _ingredients_display(row: dict, ingredient_map: dict) -> str:
    text = format_ingredient_names(row, ingredient_map)
    if text and text != "—":
        return text
    ing_only, _ = parse_nutrition_from_description(str(row.get("description", "")))
    if ing_only and ing_only not in ("手工添加", "由极客口令导入"):
        return ing_only
    return "—"


def _run_shuffle(sleep: str, load: str, meal_count: int) -> None:
    morning = _get_morning_inputs()
    _fetch_daily_menus(
        morning.get("sleep", sleep),
        morning.get("load", load),
        int(morning.get("meal_count", meal_count)),
        shuffle=True,
    )


def _render_new_dish_form(meal_type: str, dish_name: str) -> None:
    """New menu: name + ingredients text + prep time; nutrition via API analysis."""
    st.markdown(f"**新菜品 · {dish_name}**")
    st.caption("必填：食材、准备时间。填写后请点击「分析营养覆盖」，由 AI 判断七大营养类。")

    ing_key = f"new_ing_{meal_type}"
    prep_key = f"new_prep_{meal_type}"
    analysis_key = f"nutr_result_{meal_type}"

    st.text_input("菜品名称", value=dish_name, disabled=True, key=f"new_name_{meal_type}")
    ingredients_text = st.text_area(
        "食材（必填）",
        placeholder="例如：希腊酸奶、蓝莓、核桃（用顿号或逗号分隔）",
        key=ing_key,
        height=80,
    )
    prep = st.number_input(
        "准备时间（分钟，必填）",
        min_value=1,
        max_value=180,
        value=15,
        key=prep_key,
    )

    ing_text = ingredients_text.strip()
    if st.button(
        "分析营养覆盖",
        type="secondary",
        use_container_width=True,
        key=f"analyze_nutr_{meal_type}",
        disabled=not ing_text,
    ):
        with st.spinner("正在分析营养覆盖…"):
            st.session_state[analysis_key] = analyze_ingredients(ing_text)

    analysis = st.session_state.get(analysis_key)
    if analysis and ing_text:
        draft = menu_row_from_analysis(ing_text, analysis, dish_name, int(prep))
        st.caption("预计营养覆盖")
        render_coverage_badge(draft, key=f"preview_cov_{meal_type}")
        note = analysis.get("note", "")
        if note:
            st.caption(note)
        if analysis.get("unmatched"):
            st.caption("未入库食材：" + "、".join(analysis["unmatched"]))

    if st.button(
        "确认入库并加入本餐",
        type="primary",
        use_container_width=True,
        key=f"submit_new_{meal_type}",
    ):
        if not ing_text:
            st.warning("请填写食材。")
        elif not dish_name.strip():
            st.warning("菜品名称不能为空。")
        elif not analysis or not analysis.get("categories"):
            st.warning("请先点击「分析营养覆盖」。")
        else:
            menu_id = append_manual_menu(
                dish_name.strip(),
                prep_minutes=int(prep),
                ingredients_text=ing_text,
                ingredient_ids=list(analysis.get("ingredient_ids", [])),
                energy_tags=str(analysis.get("energy_tags", "手工添加")),
                nutrition_categories=list(analysis.get("categories", [])),
                meal_type=meal_type,
            )
            st.session_state.pop(analysis_key, None)
            _add_to_slot(meal_type, menu_id)
            _close_add_panel()
            st.rerun()

    st.button(
        "返回搜索",
        key=f"back_search_{meal_type}",
        use_container_width=True,
        on_click=_on_back_manual_search,
        args=(meal_type,),
    )
    st.button(
        "取消",
        key=f"cancel_create_{meal_type}",
        use_container_width=True,
        on_click=_close_add_panel,
    )


def _render_manual_add(meal_type: str, ui: dict) -> None:
    st.markdown(f"**手工添加 · {meal_type}**")
    step = ui.get("step", "search")

    if step == "create":
        _render_new_dish_form(meal_type, ui.get("draft_name", ""))
        return

    name = st.text_input(
        "菜品名称",
        placeholder="输入几个字，自动匹配库内菜品",
        key=f"manual_search_{meal_type}",
    )
    query = name.strip()
    if len(query) >= 2:
        matches = search_menus_by_keyword(query)
        if not matches.empty:
            st.caption("库内相似菜品（可直接选用）：")
            ing_map = get_ingredient_map()
            for _, m in matches.iterrows():
                row = m.to_dict()
                mid = row["menu_id"]
                cov = coverage_summary(row)
                ing_text = format_ingredient_names(row, ing_map)
                st.markdown(f"**{row['menu_name']}** · {cov}")
                st.caption(f"食材：{ing_text}")
                st.button(
                    "选用此菜品",
                    key=f"pick_match_{meal_type}_{mid}",
                    use_container_width=True,
                    on_click=_on_pick_existing,
                    args=(meal_type, mid),
                )
        else:
            st.caption("库内暂无相似名称，可作为新菜品录入。")

    if query:
        st.button(
            "确认为新菜品",
            key=f"new_dish_{meal_type}",
            use_container_width=True,
            on_click=_on_start_new_dish,
            args=(meal_type,),
        )
    else:
        st.caption("请先输入菜品名称。")

    st.button(
        "取消",
        key=f"cancel_manual_{meal_type}",
        use_container_width=True,
        on_click=_close_add_panel,
    )


def _render_add_panel(meal_type: str) -> None:
    ui = st.session_state.get("eb_add_ui")
    if not ui or ui.get("meal") != meal_type:
        return

    mode = ui["type"]
    st.markdown('<div class="eb-add-panel">', unsafe_allow_html=True)

    if mode == "manual":
        _render_manual_add(meal_type, ui)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown(f"**菜单库添加 · {meal_type}**")
    ranked = get_menus_by_pick_frequency()
    if ranked.empty:
        st.info("菜单库暂无菜品")
        st.button(
            "关闭",
            key=f"close_library_empty_{meal_type}",
            use_container_width=True,
            on_click=_close_add_panel,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    plan = _ensure_meal_plan()
    in_slot = set(plan.get(meal_type, []))
    options: list[str] = []
    labels: dict[str, str] = {}
    for _, row in ranked.iterrows():
        menu_id = row["menu_id"]
        if menu_id in in_slot:
            continue
        options.append(menu_id)
        count = int(row.get("pick_count", 0))
        suffix = f" · 已选 {count} 次" if count else ""
        labels[menu_id] = f"{row['menu_name']}{suffix}"

    if not options:
        st.info("该餐次已包含菜单库中的全部菜品")
        st.button(
            "关闭",
            key=f"close_library_full_{meal_type}",
            use_container_width=True,
            on_click=_close_add_panel,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    with st.form(key=f"form_library_{meal_type}", clear_on_submit=False):
        pick = st.selectbox(
            "选择菜品（按选用频次降序）",
            options,
            format_func=lambda x: labels.get(x, x),
        )
        submitted = st.form_submit_button("加入本餐", type="primary", use_container_width=True)
        if submitted:
            _add_to_slot(meal_type, pick)
            _close_add_panel()
            st.rerun()

    st.button(
        "取消",
        key=f"cancel_library_{meal_type}",
        use_container_width=True,
        on_click=_close_add_panel,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_meal_toolbar(
    meal_type: str,
    *,
    menu_id: str | None = None,
    show_remove: bool = False,
    show_manual: bool = False,
    show_library: bool = False,
    key_suffix: str = "row",
) -> None:
    actions: list[tuple[str, str, object | None, tuple]] = []
    if show_remove and menu_id:
        actions.append(("remove", "移除", _on_remove_dish, (meal_type, menu_id)))
    if show_manual:
        actions.append(("manual", "手工添加", _on_open_manual, (meal_type,)))
    if show_library:
        actions.append(("library", "菜单库添加", _on_open_library, (meal_type,)))
    if not actions:
        return

    cols = st.columns(len(actions))
    for col, (action, label, callback, args) in zip(cols, actions):
        with col:
            st.button(
                label,
                key=f"meal_{action}_{meal_type}_{key_suffix}",
                use_container_width=True,
                on_click=callback,
                args=args,
            )


def _render_meal_sections(
    plan: dict[str, list[str]],
    meal_slots: list[str],
    locked: bool,
) -> None:
    ingredient_map = get_ingredient_map()
    ai_fresh_ids = set(st.session_state.get("ai_fresh_menu_ids") or [])

    for meal_type in meal_slots:
        menu_ids = plan.get(meal_type, [])

        with st.container(border=True):
            if not menu_ids:
                st.caption(f"{meal_type} · 暂无菜品")
                if not locked:
                    _render_meal_toolbar(
                        meal_type,
                        show_manual=True,
                        show_library=True,
                        key_suffix="empty",
                    )
                    _render_add_panel(meal_type)
                continue

            for idx, menu_id in enumerate(menu_ids):
                row = get_menu_by_id(menu_id)
                if not row:
                    continue

                if idx > 0:
                    st.divider()

                render_meal_headline(
                    meal_type,
                    row,
                    idx=idx,
                    locked=locked,
                    widget_key=f"head_{meal_type}_{menu_id}_{idx}",
                    ai_fresh=menu_id in ai_fresh_ids,
                )

                ingredients = _ingredients_display(row, ingredient_map)
                st.caption(f"食材：{ingredients}")

                if not locked:
                    single = len(menu_ids) == 1
                    if single:
                        _render_meal_toolbar(
                            meal_type,
                            menu_id=menu_id,
                            show_remove=True,
                            show_manual=True,
                            show_library=True,
                            key_suffix=menu_id,
                        )
                    else:
                        _render_meal_toolbar(
                            meal_type,
                            menu_id=menu_id,
                            show_remove=True,
                            key_suffix=f"{menu_id}_rm",
                        )

            if not locked and len(menu_ids) > 1:
                _render_meal_toolbar(
                    meal_type,
                    show_manual=True,
                    show_library=True,
                    key_suffix="footer",
                )

            if not locked:
                _render_add_panel(meal_type)


def _on_unlock_plan() -> None:
    plan = _ensure_meal_plan()
    st.session_state.menu_locked = False
    st.session_state.final_daily_list = []
    st.session_state.final_meal_plan = _empty_meal_plan()
    _persist_plan(plan, confirmed=False)


def _save_favorite_menu() -> bool:
    plan = _ensure_meal_plan()
    menu_ids = _flatten_plan(plan)
    if not menu_ids:
        return False
    today = st.session_state.get("today_date", date.today().isoformat())
    save_favorite_menu_set(menu_ids, today)
    return True


def render() -> None:
    init_database()
    hydrate_today_state()
    today_iso = st.session_state.get("today_date", date.today().isoformat())

    legacy_act = pop_query_param("act")

    locked = st.session_state.get("menu_locked", False)

    if locked and st.session_state.get("final_daily_list"):
        st.success("今日就餐计划已确认 · 可前往「回顾」填写评价。")

    if st.session_state.pop("menu_fav_flash", False):
        st.success("已收藏此套菜单 · 可在「分享 → 收藏菜单 → 全天菜单」查看。")

    morning = _get_morning_inputs()
    meal_count = int(morning.get("meal_count", st.session_state.get("morning_meal_count", 3)))
    meal_slots = _active_meal_slots(meal_count)

    plan = _ensure_meal_plan()
    menu_ids = _flatten_plan(plan)
    has_context = _has_morning_context(today_iso)
    planning_phase = len(menu_ids) == 0

    sleep = st.session_state.get("morning_sleep", "良好")
    load = st.session_state.get("morning_load", "中等")

    if legacy_act == "gen" and planning_phase and not locked and has_context:
        _run_generate(sleep, load, int(meal_count))
        st.rerun()

    if legacy_act == "shuffle" and not planning_phase and not locked and has_context:
        _run_shuffle(sleep, load, int(meal_count))
        st.rerun()

    if planning_phase:
        if not has_context:
            st.info("请先在「回顾」页填写并保存晨间三问，再回来生成菜单。")
        else:
            st.info("开始规划餐食，今天想吃什么？")

        left = _library_gens_remaining()
        if left > 0:
            st.caption(f"今日前 {LIBRARY_GEN_MAX} 次从菜品库生成，还可库内生成 {left} 次。")
        elif has_api_key():
            st.caption("下一次生成将由 AI 创作全新菜品。")

        if st.button(
            "🍴 生成菜单",
            type="primary",
            use_container_width=True,
            key="btn_gen_menu",
            disabled=not has_context,
        ):
            _run_generate(sleep, load, int(meal_count))
            st.rerun()
        return

    note = st.session_state.pop("last_gen_note", None)
    if note:
        if st.session_state.get("last_gen_source") == "api":
            st.success(note)
        else:
            st.info(note)

    left = _library_gens_remaining()
    if left > 0:
        st.caption(f"还可库内换套 {left} 次，之后将启用 AI 创作。")
    elif has_api_key():
        st.caption("下一次换套将由 AI 创作全新菜品。")

    if not locked:
        if st.button(
            "🔀 换套菜单",
            type="primary",
            use_container_width=True,
            key="btn_shuffle_menu",
            disabled=not has_context,
        ):
            _run_shuffle(sleep, load, int(meal_count))
            st.rerun()
    elif locked:
        st.caption("如需修改菜品，请先重新编辑。")
        if st.button("重新编辑菜单", use_container_width=True, key="btn_unlock_plan"):
            _on_unlock_plan()
            st.rerun()

    section_title("fa-clipboard-list", "今日菜单")

    if locked:
        fp = st.session_state.get("final_meal_plan") or {}
        display_plan = fp if _flatten_plan(fp) else _plan_from_menu_ids(
            list(st.session_state.get("final_daily_list", []))
        )
    else:
        display_plan = plan
    _render_meal_sections(display_plan, meal_slots, locked)

    if not locked:
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button(
                "确认今日就餐计划",
                type="primary",
                use_container_width=True,
                key="confirm_plan",
            ):
                st.session_state.final_meal_plan = {k: list(v) for k, v in plan.items()}
                st.session_state.final_daily_list = _flatten_plan(plan)
                st.session_state.menu_locked = True
                st.session_state.eb_add_ui = None
                _persist_plan(plan, confirmed=True)
                st.rerun()
        with action_col2:
            if st.button("❤️ 收藏此菜单", use_container_width=True, key="btn_fav_menu"):
                if _save_favorite_menu():
                    st.toast("已收藏此套菜单", icon="❤️")
                    st.session_state.menu_fav_flash = True
                    st.rerun()
                else:
                    st.warning("当前没有可收藏的菜单。")
    else:
        if st.button("❤️ 收藏此菜单", use_container_width=True, key="btn_fav_menu_locked"):
            if _save_favorite_menu():
                st.toast("已收藏此套菜单", icon="❤️")
                st.session_state.menu_fav_flash = True
                st.rerun()
            else:
                st.warning("当前没有可收藏的菜单。")
