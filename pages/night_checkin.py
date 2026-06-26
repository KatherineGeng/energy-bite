"""回顾页 — 晨间三问 + 晚间回顾."""

from __future__ import annotations

import streamlit as st

from src.algorithm import recalculate_weights
from src.constants import LOAD_OPTIONS, MEAL_COUNT_OPTIONS, SLEEP_OPTIONS
from src.database import (
    append_log,
    get_menu_row,
    load_favorites_dishes,
    load_morning_context,
    remove_favorite_dish,
    save_favorite_dish,
    save_favorite_menu_set,
)
from src.review_persistence import (
    apply_review_draft_to_session,
    on_review_field_change,
    persist_review_draft,
    persist_review_progress,
    try_save_morning_section,
)
from src.review_ui import (
    render_dish_header_with_favorite,
    render_option_picker,
    render_score_picker,
)
from src.session_hydrate import apply_morning_context_from_disk, get_confirmed_plan
from src.theme import ACCENT, section_title
from src.user_profile import morning_greeting, nickname


def _dish_favorited_in_db(menu_id: str, today: str) -> bool:
    df = load_favorites_dishes()
    if df.empty:
        return False
    return not df[(df["menu_id"] == menu_id) & (df["date"] == today)].empty


def _toggle_dish_favorite(menu_id: str, today: str, menu_ids: list[str]) -> None:
    currently = _dish_favorited_in_db(menu_id, today)
    new_val = not currently
    st.session_state[f"review_{menu_id}_fav_dish"] = new_val
    if new_val:
        save_favorite_dish(menu_id, today)
    else:
        remove_favorite_dish(menu_id, today)
    persist_review_progress(today, menu_ids)


def _hydrate_review_favorites(menu_ids: list[str], today: str) -> None:
    df = load_favorites_dishes()
    if df.empty:
        return
    for menu_id in menu_ids:
        key = f"review_{menu_id}_fav_dish"
        if key not in st.session_state:
            hit = not df[(df["menu_id"] == menu_id) & (df["date"] == today)].empty
            st.session_state[key] = hit


def _ritual_line() -> str:
    from src.user_profile import nickname

    name = nickname()
    if name:
        return f"{name}度过了快乐健康的一天"
    return "我度过了快乐健康的一天"


def _review_scores_complete(menu_ids: list[str]) -> bool:
    for menu_id in menu_ids:
        if st.session_state.get(f"review_{menu_id}_operation") is None:
            return False
        if st.session_state.get(f"review_{menu_id}_nps") is None:
            return False
    if st.session_state.get("review_day_mood") is None:
        return False
    if st.session_state.get("review_day_energy") is None:
        return False
    return True


def _inject_review_card_css() -> None:
    st.markdown(
        f"""
        <style>
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: rgba(255, 255, 255, 0.78) !important;
            border: 1px solid rgba(141, 163, 153, 0.32) !important;
            border-radius: 14px !important;
            padding: 0.35rem 0.5rem !important;
            margin-bottom: 0.65rem !important;
            box-shadow: 0 3px 16px rgba(30, 41, 59, 0.05) !important;
        }}
        .eb-dish-name {{
            font-family: 'Noto Serif SC', serif;
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
            color: #1E293B;
            line-height: 1.35;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {{
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 0.35rem !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {{
            flex: 1 1 auto !important;
            min-width: 0 !important;
            width: auto !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child:not(:only-child) {{
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 4.5rem !important;
            max-width: 5.5rem !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] .stButton > button {{
            min-height: 2rem !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:first-of-type .stButton > button {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #64748B !important;
            font-size: 0.92rem !important;
            font-weight: 500 !important;
            padding: 0.1rem 0.2rem !important;
            white-space: nowrap !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"]:first-of-type .stButton > button[kind="primary"] {{
            color: #EF4444 !important;
            background: transparent !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPills"] > div {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            gap: 0.28rem !important;
            width: 100% !important;
            margin: 0.15rem 0 0.5rem !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPills"] button {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            min-height: 2.4rem !important;
            border-radius: 10px !important;
            border: 1px solid rgba(141, 163, 153, 0.45) !important;
            background: rgba(255, 255, 255, 0.9) !important;
            color: #334155 !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            box-shadow: none !important;
            padding: 0 !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPills"] button[aria-pressed="true"] {{
            background: {ACCENT} !important;
            border-color: {ACCENT} !important;
            color: #fff !important;
        }}
        .eb-morning-block [data-testid="stPills"] button,
        .eb-day-status-block [data-testid="stPills"] button {{
            font-size: 0.82rem !important;
        }}
        .eb-morning-block [data-testid="stPills"] > div,
        .eb-day-status-block [data-testid="stPills"] > div,
        .eb-review-picks + div [data-testid="stPills"] > div,
        .eb-review-picks ~ div [data-testid="stPills"] > div {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: stretch !important;
            gap: 0.28rem !important;
            width: 100% !important;
            margin: 0.15rem 0 0.5rem !important;
        }}
        .eb-morning-block [data-testid="stPills"] button,
        .eb-day-status-block [data-testid="stPills"] button,
        .eb-review-picks + div [data-testid="stPills"] button,
        .eb-review-picks ~ div [data-testid="stPills"] button {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            min-height: 2.4rem !important;
            border-radius: 10px !important;
            border: 1px solid rgba(141, 163, 153, 0.45) !important;
            background: rgba(255, 255, 255, 0.9) !important;
            color: #334155 !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            box-shadow: none !important;
            padding: 0 !important;
        }}
        .eb-morning-block [data-testid="stPills"] button[aria-pressed="true"],
        .eb-day-status-block [data-testid="stPills"] button[aria-pressed="true"],
        .eb-review-picks + div [data-testid="stPills"] button[aria-pressed="true"],
        .eb-review-picks ~ div [data-testid="stPills"] button[aria-pressed="true"] {{
            background: {ACCENT} !important;
            border-color: {ACCENT} !important;
            color: #fff !important;
        }}
        .eb-score-label {{
            font-family: 'Noto Serif SC', serif;
            font-size: 1.05rem;
            font-weight: 600;
            color: #1E293B;
            margin: 0.35rem 0 0.15rem;
        }}
        .eb-morning-saved-banner {{
            background: rgba(46, 125, 96, 0.1);
            border: 1px solid rgba(46, 125, 96, 0.35);
            border-radius: 10px;
            padding: 0.55rem 0.7rem;
            margin: 0.35rem 0 0.65rem;
            color: #1E5E46;
            font-size: 0.92rem;
        }}
        .eb-ritual {{
            text-align: center;
            font-size: 1.1rem;
            color: {ACCENT};
            font-family: 'Noto Serif SC', serif;
            margin: 0.75rem 0 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _morning_saved(today_iso: str) -> bool:
    if st.session_state.get("morning_context_loaded") == today_iso:
        return True
    return load_morning_context(today_iso) is not None


def _morning_saved_summary(today_iso: str) -> dict:
    inputs = st.session_state.get("morning_inputs") or {}
    if inputs.get("sleep") and inputs.get("load") and inputs.get("meal_count"):
        return inputs
    ctx = load_morning_context(today_iso)
    return ctx or {}


@st.fragment
def _morning_review_fragment(today_iso: str) -> None:
    apply_morning_context_from_disk(today_iso)
    section_title("fa-sun", "晨间三问")
    st.caption(morning_greeting())

    saved = _morning_saved(today_iso)
    if saved:
        summary = _morning_saved_summary(today_iso)
        st.markdown(
            f'<div class="eb-morning-saved-banner">'
            f"✓ <strong>今日晨间记录已保存</strong><br>"
            f"睡眠：{summary.get('sleep', '—')} · 消耗：{summary.get('load', '—')} · "
            f"餐数：{summary.get('meal_count', '—')} 餐"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("请依次选择下方三项，选齐后自动保存到云端。")

    def _on_morning_pick() -> None:
        if try_save_morning_section(today_iso):
            st.session_state.record_saved_flash = True

    st.markdown('<div class="eb-morning-block">', unsafe_allow_html=True)
    render_option_picker(
        "一、昨晚睡眠状态",
        "",
        "morning_sleep",
        SLEEP_OPTIONS,
        on_pick=_on_morning_pick,
    )
    render_option_picker(
        "二、今日脑力/体力消耗",
        "",
        "morning_load",
        LOAD_OPTIONS,
        on_pick=_on_morning_pick,
    )
    render_option_picker(
        "三、今日一人食餐数",
        "",
        "morning_meal_count",
        MEAL_COUNT_OPTIONS,
        format_label=lambda x: f"{x} 餐",
        on_pick=_on_morning_pick,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pop("record_saved_flash", False):
        st.success("晨间记录已保存 · 可前往「菜单」生成今日餐食。")


@st.fragment
def _dishes_review_fragment(confirmed: dict) -> None:
    menu_ids: list[str] = list(confirmed["menu_ids"])
    today = confirmed["date"]
    snapshots = confirmed.get("snapshots", {})

    apply_review_draft_to_session(today, menu_ids)
    _hydrate_review_favorites(menu_ids, today)

    def _on_dish_pick() -> None:
        persist_review_progress(today, menu_ids)

    for menu_id in menu_ids:
        menu_row = get_menu_row(menu_id, snapshots)
        if not menu_row:
            continue

        with st.container(border=True):
            meal_type = str(menu_row.get("meal_type", "")).strip()
            dish_name = menu_row["menu_name"]
            render_dish_header_with_favorite(
                meal_type,
                dish_name,
                menu_id,
                today,
                on_toggle=lambda m=menu_id: _toggle_dish_favorite(m, today, menu_ids),
            )
            render_score_picker(
                "操作从容度 (1-5分)",
                "1：极其匆忙 → 5：优雅享受",
                f"review_{menu_id}_operation",
                on_pick=_on_dish_pick,
            )
            render_score_picker(
                "这道菜我还想再吃一次 (1-5分)",
                "1：极不赞成 → 5：极度赞成",
                f"review_{menu_id}_nps",
                on_pick=_on_dish_pick,
            )

    st.checkbox(
        "🌟 收藏今日整套全天菜单",
        key="review_fav_full_day",
        on_change=on_review_field_change,
        args=(today, menu_ids),
    )


@st.fragment
def _day_status_fragment(confirmed: dict) -> None:
    menu_ids: list[str] = list(confirmed["menu_ids"])
    morning = st.session_state.get("morning_inputs", {})
    today = confirmed["date"]

    section_title("fa-heart-pulse", "全天个人状态")

    def _on_day_pick() -> None:
        persist_review_progress(today, menu_ids)

    st.markdown('<div class="eb-day-status-block">', unsafe_allow_html=True)
    render_score_picker(
        "情绪状态 (1-5分)",
        "1分：很低落 → 5分：很愉悦",
        "review_day_mood",
        on_pick=_on_day_pick,
    )
    render_score_picker(
        "精力水平 (1-5分)",
        "1分：很疲惫 → 5分：精力充沛",
        "review_day_energy",
        on_pick=_on_day_pick,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("完成今日回顾，去生成日志", type="primary", use_container_width=True, key="review_submit"):
        persist_review_draft(today, menu_ids)
        if not _review_scores_complete(menu_ids):
            st.warning("请完成所有评分后再提交。")
            return
        day_mood = st.session_state.get("review_day_mood")
        day_energy = st.session_state.get("review_day_energy")
        log_ids: list[str] = []
        for menu_id in menu_ids:
            dish_fav = bool(st.session_state.get(f"review_{menu_id}_fav_dish", False))
            log_id = append_log(
                date=today,
                menu_id=menu_id,
                nps_score=int(st.session_state[f"review_{menu_id}_nps"]),
                operation_score=int(st.session_state[f"review_{menu_id}_operation"]),
                mood_score=int(day_mood),
                energy_score=int(day_energy),
                is_favorited=dish_fav,
                sleep_quality=morning.get("sleep", ""),
                brain_body_load=morning.get("load", ""),
                meal_count=morning.get("meal_count"),
            )
            log_ids.append(log_id)
            if dish_fav:
                save_favorite_dish(menu_id, today)

        if st.session_state.get("review_fav_full_day"):
            save_favorite_menu_set(menu_ids, today)

        persist_review_draft(today, menu_ids, completed=True)
        recalculate_weights()
        st.session_state.last_log_id = log_ids[-1] if log_ids else None
        st.session_state.review_complete = True
        st.session_state.current_page = "export"
        st.rerun()

    st.markdown(f'<p class="eb-ritual">{_ritual_line()}</p>', unsafe_allow_html=True)


def render() -> None:
    from src.app_time import beijing_today_iso

    today_iso = st.session_state.get("today_date", beijing_today_iso())
    _inject_review_card_css()
    _morning_review_fragment(today_iso)

    confirmed = get_confirmed_plan(today_iso)
    if not confirmed:
        st.warning("请先在「菜单」页确认今日就餐计划，再填写下方晚间回顾。")
        return

    menu_ids = list(confirmed["menu_ids"])
    today = confirmed["date"]
    apply_review_draft_to_session(today, menu_ids)

    st.divider()
    section_title("fa-moon", "晚间回顾")
    st.caption("以下为您在「今日菜单」中已确认的就餐计划。")
    section_title("fa-utensils", "今日餐食评价")
    st.markdown('<div class="eb-evening-review">', unsafe_allow_html=True)
    _dishes_review_fragment(confirmed)
    st.markdown("</div>", unsafe_allow_html=True)
    _day_status_fragment(confirmed)
