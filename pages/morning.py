"""Morning workbench — 简愈一人食."""

from __future__ import annotations

from datetime import date
from urllib.parse import quote

import streamlit as st

from src.constants import LIBRARY_GEN_MAX
from src.ai_menu import suggest_daily_menus_api
from src.database import (
    append_manual_menu,
    get_ingredient_map,
    get_menu_by_id,
    get_menu_row,
    get_menus_by_pick_frequency,
    load_daily_meal_plan,
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
from src.favorite_recommend import recent_favorite_menu_candidates
from src.session_hydrate import get_confirmed_plan
from src.llm_client import has_api_key
from src.coverage_widget import render_daily_coverage_table
from src.nutrition import coverage_summary
from src.nutrition_api import analyze_ingredients, parse_nutrition_from_description
from src.mobile_ui import (
    MENU_GEN_ICON,
    render_meal_action_row,
    render_meal_dish_header,
    render_primary_action_link,
)
from src.nav_params import append_nav_params
from src.query_nav import pop_query_param
from src.recommendation import format_ingredient_names, get_daily_menus
from src.theme import section_title
from src.user_profile import planning_prompt


def _page_query_href(**params: str) -> str:
    page = st.session_state.get("current_page", "morning")
    parts = [f"nav={quote(page)}"]
    for key, val in params.items():
        if val:
            parts.append(f"{quote(key)}={quote(val)}")
    return append_nav_params("?" + "&".join(parts))


def _render_link_row(links: list[tuple[str, str, str]]) -> None:
    """Render horizontal HTML link buttons: (href, label, extra_class)."""
    parts: list[str] = []
    for href, label, extra in links:
        cls = "eb-meal-action-btn" + (f" {extra}" if extra else "")
        parts.append(f'<a class="{cls}" href="{href}">{label}</a>')
    st.markdown(f'<div class="eb-meal-action-row">{"".join(parts)}</div>', unsafe_allow_html=True)


def _flash_success(msg: str) -> None:
    st.session_state.eb_flash_success = msg


def _flash(msg: str) -> None:
    st.session_state.eb_flash = msg


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
    from src.db_config import postgres_enabled

    snapshots = save_daily_meal_plan(today, plan, confirmed=confirmed)
    if snapshots:
        st.session_state.eb_plan_snapshots = snapshots

    if postgres_enabled():
        return

    saved = load_daily_meal_plan(today)
    if saved:
        st.session_state.eb_plan_snapshots = saved.get("snapshots", {})
    from src.plan_bootstrap import persist_plan_to_browser

    persist_plan_to_browser(
        today,
        plan,
        confirmed=confirmed,
        snapshots=st.session_state.get("eb_plan_snapshots", {}),
    )


def _menu_snapshots() -> dict:
    return st.session_state.get("eb_plan_snapshots", {})


def _resolve_menu(menu_id: str) -> dict | None:
    return get_menu_row(menu_id, _menu_snapshots())


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
    plan = {meal: list(ids) for meal, ids in _ensure_meal_plan().items()}
    plan[meal_type] = [mid for mid in plan.get(meal_type, []) if mid != menu_id]
    st.session_state.menu_locked = False
    st.session_state.final_daily_list = []
    st.session_state.final_meal_plan = _empty_meal_plan()
    st.session_state.eb_add_ui = None
    _sync_draft_from_plan(plan)


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


def _try_confirm_new_dish(
    meal_type: str,
    *,
    ing_text: str | None = None,
    prep: int | None = None,
) -> bool:
    ui = st.session_state.get("eb_add_ui") or {}
    if ui.get("step") != "create":
        return False
    dish_name = str(ui.get("draft_name", "")).strip()
    ing_key = f"new_ing_{meal_type}"
    prep_key = f"new_prep_{meal_type}"
    analysis_key = f"nutr_result_{meal_type}"
    if ing_text is None:
        ing_text = str(st.session_state.get(ing_key, "")).strip()
    else:
        ing_text = str(ing_text).strip()
    if prep is None:
        prep = int(st.session_state.get(prep_key, 15))
    else:
        prep = int(prep)
    analysis = st.session_state.get(analysis_key)

    if not ing_text:
        _flash("请填写食材。")
        return False
    if not dish_name:
        _flash("菜品名称不能为空。")
        return False

    if not analysis or not analysis.get("categories"):
        analysis = analyze_ingredients(ing_text)
        st.session_state[analysis_key] = analysis

    if not analysis or not analysis.get("categories"):
        _flash("营养分析失败，请检查食材描述。")
        return False

    menu_id = append_manual_menu(
        dish_name,
        prep_minutes=prep,
        ingredients_text=ing_text,
        ingredient_ids=[],  # nutrition from categories; display uses raw text
        energy_tags=str(analysis.get("energy_tags", "手工添加")),
        nutrition_categories=list(analysis.get("categories", [])),
        meal_type=meal_type,
    )
    st.session_state.pop(analysis_key, None)
    _add_to_slot(meal_type, menu_id)
    _close_add_panel()
    _flash_success(f"已添加「{dish_name}」")
    return True


def _toggle_coverage_table() -> None:
    st.session_state.eb_show_coverage = not st.session_state.get("eb_show_coverage", False)


def _confirm_today_plan() -> None:
    plan = _ensure_meal_plan()
    st.session_state.final_meal_plan = {k: list(v) for k, v in plan.items()}
    st.session_state.final_daily_list = _flatten_plan(plan)
    st.session_state.menu_locked = True
    st.session_state.eb_add_ui = None
    _persist_plan(plan, confirmed=True)
    from src.database import record_menu_archive

    today = st.session_state.get("today_date", date.today().isoformat())
    record_menu_archive(today, st.session_state.final_daily_list)


def _on_favorite_menu() -> None:
    if _save_favorite_menu():
        st.session_state.menu_fav_flash = True
    else:
        st.session_state.eb_flash = "当前没有可收藏的菜单。"


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


def _confirmed_menu_ids_today(today_iso: str) -> list[str]:
    confirmed = get_confirmed_plan(today_iso)
    if confirmed and confirmed.get("menu_ids"):
        return list(confirmed["menu_ids"])
    return []


def _favorite_menu_candidates(today_iso: str) -> list[dict]:
    return recent_favorite_menu_candidates(
        within_days=5,
        exclude_menu_ids=_confirmed_menu_ids_today(today_iso),
    )


def _apply_favorite_menu(menu_ids: list[str], *, meal_count: int) -> bool:
    plan = _plan_from_menu_ids(menu_ids)
    slots = _active_meal_slots(meal_count)
    trimmed = {slot: list(plan.get(slot, [])) for slot in slots}
    if not _flatten_plan(trimmed):
        return False
    _sync_draft_from_plan(trimmed)
    st.session_state.today_menus = []
    st.session_state.last_gen_source = "favorite"
    st.session_state.last_gen_note = "来自收藏菜单推荐"
    st.session_state.ai_fresh_menu_ids = []
    return True


def _try_auto_favorite_recommendation(today_iso: str, meal_count: int) -> bool:
    if st.session_state.get("eb_fav_auto_date") == today_iso:
        return False
    st.session_state.eb_fav_auto_date = today_iso
    candidates = _favorite_menu_candidates(today_iso)
    if not candidates:
        return False
    return _apply_favorite_menu(candidates[0]["menu_ids"], meal_count=meal_count)


def _run_recommend_menu(sleep: str, load: str, meal_count: int, today_iso: str) -> None:
    candidates = _favorite_menu_candidates(today_iso)
    if candidates:
        _apply_favorite_menu(candidates[0]["menu_ids"], meal_count=meal_count)
        return
    _fetch_daily_menus(sleep, load, int(meal_count), shuffle=False)


def _run_generate(sleep: str, load: str, meal_count: int) -> None:
    st.session_state.morning_inputs = {"sleep": sleep, "load": load, "meal_count": int(meal_count)}
    _fetch_daily_menus(sleep, load, int(meal_count), shuffle=False)
    st.session_state.today_date = date.today().isoformat()


def _ingredients_display(row: dict, ingredient_map: dict) -> str:
    """Show user-entered text for manual dishes; library names otherwise."""
    ing_only, _ = parse_nutrition_from_description(str(row.get("description", "")))
    if ing_only and ing_only not in ("手工添加", "由极客口令导入"):
        return ing_only
    text = format_ingredient_names(row, ingredient_map)
    if text and text != "—":
        return text
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
    """New menu: name + ingredients + prep; confirm auto-analyzes and closes panel."""
    st.markdown(f"**新菜品 · {dish_name}**")
    st.caption("必填：食材、准备时间。点击确认后自动分析营养并加入本餐。")

    ing_key = f"new_ing_{meal_type}"
    prep_key = f"new_prep_{meal_type}"

    st.text_input("菜品名称", value=dish_name, disabled=True, key=f"new_name_{meal_type}")
    ing_text = st.text_area(
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

    if st.button(
        "确认入库并加入本餐",
        type="primary",
        use_container_width=True,
        key=f"confirm_new_{meal_type}",
    ):
        if _try_confirm_new_dish(meal_type, ing_text=ing_text, prep=prep):
            st.rerun()


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
    if query:
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
        if st.button(
            "确认为新菜品",
            type="primary",
            use_container_width=True,
            key=f"start_new_{meal_type}",
        ):
            _on_start_new_dish(meal_type)
            st.rerun()
    else:
        st.caption("请先输入菜品名称。")


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
            key=f"lib_close_empty_{meal_type}",
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
            key=f"lib_close_full_{meal_type}",
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
        key=f"lib_cancel_{meal_type}",
        use_container_width=True,
        on_click=_close_add_panel,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _apply_ui_query_actions() -> None:
    ui_act = pop_query_param("ui_act")
    if not ui_act:
        return
    meal = pop_query_param("meal")
    if ui_act == "back_search" and meal:
        _on_back_manual_search(meal)
        st.rerun()
    elif ui_act == "cancel_add":
        _close_add_panel()
        st.rerun()
    elif ui_act == "confirm_new" and meal:
        if _try_confirm_new_dish(meal):
            st.rerun()
    elif ui_act == "new_dish" and meal:
        _on_start_new_dish(meal)
        st.rerun()


def _apply_meal_query_actions() -> None:
    meal_act = pop_query_param("meal_act")
    meal = pop_query_param("meal")
    mid = pop_query_param("mid")
    if not meal_act or not meal:
        return
    if meal_act == "remove" and mid:
        _on_remove_dish(meal, mid)
        st.rerun()
    elif meal_act == "manual":
        _on_open_manual(meal)
        st.rerun()
    elif meal_act == "library":
        _on_open_library(meal)
        st.rerun()


def _render_meal_toolbar_items(
    meal_type: str,
    items: list[tuple[str, str, str | None]],
) -> None:
    if items:
        render_meal_action_row(meal_type, items)


def _render_meal_toolbar(
    meal_type: str,
    *,
    menu_id: str | None = None,
    show_remove: bool = False,
    show_manual: bool = False,
    show_library: bool = False,
    key_suffix: str = "row",
) -> None:
    """HTML link row — horizontal on mobile Safari."""
    del key_suffix
    items: list[tuple[str, str, str | None]] = []
    if show_remove and menu_id:
        items.append(("remove", "移除", menu_id))
    if show_manual:
        items.append(("manual", "手工添加", None))
    if show_library:
        items.append(("library", "菜单库添加", None))
    if items:
        render_meal_action_row(meal_type, items)


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
                row = _resolve_menu(menu_id)
                if not row:
                    if idx > 0:
                        st.divider()
                    st.caption("服务器更新后库内记录可能清空，请点「移除」后重新添加。")
                    if not locked and len(menu_ids) > 1:
                        href = append_nav_params(
                            f"?nav=morning&meal_act=remove&meal={quote(meal_type)}&mid={quote(menu_id)}"
                        )
                        st.markdown(
                            f'<div class="eb-meal-head-row">'
                            f'<div class="eb-meal-head-title"><strong>{meal_type}</strong> · 手工菜记录已过期（{menu_id}）</div>'
                            f'<a class="eb-meal-head-remove" href="{href}">移除</a>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"**{meal_type}** · 手工菜记录已过期（{menu_id}）")
                    continue

                if idx > 0:
                    st.divider()

                multi = len(menu_ids) > 1
                render_meal_dish_header(
                    meal_type,
                    row,
                    idx=idx,
                    menu_id=menu_id,
                    show_remove=not locked and multi,
                    ai_fresh=menu_id in ai_fresh_ids,
                )

                tags_str = str(row.get("energy_tags", "")).replace("·", " · ")
                prep = f"⏱ {row['prep_minutes']} min"
                st.markdown(
                    f'<span class="eb-meal-meta-inline">{tags_str} · {prep}</span>',
                    unsafe_allow_html=True,
                )

                ingredients = _ingredients_display(row, ingredient_map)
                st.caption(f"食材：{ingredients}")

            if not locked:
                footer: list[tuple[str, str, str | None]] = [
                    ("manual", "手工添加", None),
                    ("library", "菜单库添加", None),
                ]
                if len(menu_ids) == 1:
                    footer.insert(0, ("remove", "移除", menu_ids[0]))
                _render_meal_toolbar_items(meal_type, footer)

            if not locked:
                _render_add_panel(meal_type)


def _on_unlock_plan() -> None:
    plan = _ensure_meal_plan()
    st.session_state.menu_locked = False
    st.session_state.final_daily_list = []
    st.session_state.final_meal_plan = _empty_meal_plan()
    _persist_plan(plan, confirmed=False)


def _render_bottom_action_row(*, locked: bool) -> None:
    """Three horizontal HTML links — mobile Safari safe."""
    page = st.session_state.get("current_page", "morning")
    base = append_nav_params(f"?nav={quote(page)}")
    confirm_label = "重新编辑" if locked else "确认今日菜单"
    confirm_act = "unlock" if locked else "confirm"
    confirm_cls = "" if locked else " primary"
    st.markdown(
        f'<div class="eb-meal-action-row eb-bottom-action-row">'
        f'<a class="eb-meal-action-btn" href="{base}&bottom_act=cov">营养覆盖</a>'
        f'<a class="eb-meal-action-btn{confirm_cls}" href="{base}&bottom_act={confirm_act}">{confirm_label}</a>'
        f'<a class="eb-meal-action-btn" href="{base}&bottom_act=fav">收藏菜单</a>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _apply_bottom_query_actions() -> None:
    act = pop_query_param("bottom_act")
    if not act:
        return
    if act == "cov":
        _toggle_coverage_table()
        st.rerun()
    elif act == "confirm":
        _confirm_today_plan()
        st.rerun()
    elif act == "unlock":
        _on_unlock_plan()
        st.rerun()
    elif act == "fav":
        _on_favorite_menu()
        st.rerun()


def _save_favorite_menu() -> bool:
    plan = _ensure_meal_plan()
    menu_ids = _flatten_plan(plan)
    if not menu_ids:
        return False
    today = st.session_state.get("today_date", date.today().isoformat())
    save_favorite_menu_set(menu_ids, today)
    return True


def render() -> None:
    today_iso = st.session_state.get("today_date", date.today().isoformat())

    legacy_act = pop_query_param("act")
    _apply_bottom_query_actions()
    _apply_ui_query_actions()
    _apply_meal_query_actions()

    if msg := st.session_state.pop("eb_flash", None):
        st.warning(msg)

    if msg := st.session_state.pop("eb_flash_success", None):
        st.success(msg)

    locked = st.session_state.get("menu_locked", False)

    if locked and st.session_state.get("final_daily_list"):
        st.success("今日就餐计划已确认 · 可前往「回顾」填写评价。")

    if st.session_state.pop("menu_fav_flash", False):
        st.success("已收藏此套菜单 · 可在「我的 → 全天菜单」查看。")

    morning = _get_morning_inputs()
    meal_count = int(morning.get("meal_count", st.session_state.get("morning_meal_count", 3)))
    meal_slots = _active_meal_slots(meal_count)

    plan = _ensure_meal_plan()
    menu_ids = _flatten_plan(plan)
    planning_phase = len(menu_ids) == 0

    sleep = morning.get("sleep", st.session_state.get("morning_sleep", "良好"))
    load = morning.get("load", st.session_state.get("morning_load", "中等"))

    if legacy_act == "gen" and planning_phase and not locked:
        with st.spinner("正在推荐菜单…"):
            _run_recommend_menu(sleep, load, int(meal_count), today_iso)
        st.rerun()

    if planning_phase and not locked:
        if _try_auto_favorite_recommendation(today_iso, int(meal_count)):
            st.rerun()

    if legacy_act == "shuffle" and not planning_phase and not locked:
        with st.spinner("正在换套菜单…"):
            _run_shuffle(sleep, load, int(meal_count))
        st.rerun()

    if planning_phase:
        st.info(planning_prompt())
        render_primary_action_link("gen", MENU_GEN_ICON, "推荐菜单")
        return

    note = st.session_state.pop("last_gen_note", None)
    gen_source = st.session_state.get("last_gen_source")
    left = _library_gens_remaining()

    shuffle_hint = ""
    if not locked:
        if left > 0:
            shuffle_hint = f"还可库内换套 {left} 次，之后将启用 AI 创作。"
        elif has_api_key():
            shuffle_hint = "下一次换套将由 AI 创作全新菜品。"

    if note and shuffle_hint:
        banner = f"{note} {shuffle_hint}"
    elif note:
        banner = note
    elif shuffle_hint:
        banner = shuffle_hint
    else:
        banner = None

    if banner:
        if gen_source in ("api", "favorite") and note:
            st.success(banner)
        else:
            st.info(banner)

    if not locked:
        render_primary_action_link("shuffle", "🔀", "换套菜单")
    elif locked:
        st.caption("如需修改菜品，请点底部「重新编辑」。")

    menu_section = "推荐菜单" if gen_source == "favorite" and not locked else "今日菜单"
    section_title("fa-clipboard-list", menu_section)

    if locked:
        fp = st.session_state.get("final_meal_plan") or {}
        display_plan = fp if _flatten_plan(fp) else _plan_from_menu_ids(
            list(st.session_state.get("final_daily_list", []))
        )
    else:
        display_plan = plan
    _render_meal_sections(display_plan, meal_slots, locked)

    if st.session_state.get("eb_show_coverage"):
        render_daily_coverage_table(display_plan, meal_slots, _resolve_menu)

    _render_bottom_action_row(locked=locked)
