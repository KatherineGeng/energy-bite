"""回顾页 — 晨间三问 + 晚间回顾."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.algorithm import recalculate_weights
from src.constants import LOAD_OPTIONS, MEAL_COUNT_OPTIONS, SLEEP_OPTIONS
from src.database import (
    append_log,
    get_menu_by_id,
    init_database,
    save_favorite_dish,
    save_favorite_menu_set,
    save_morning_context,
)
from src.review_ui import render_dish_favorite_heart
from src.session_hydrate import get_confirmed_plan, hydrate_today_state
from src.theme import ACCENT, section_title
from src.user_profile import morning_greeting, nickname

SCORE_OPTIONS = [1, 2, 3, 4, 5]


def _score_btn(x: int) -> str:
    return f"{x}分"


def _ritual_line() -> str:
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
        .eb-dish-head-row [data-testid="stHorizontalBlock"] {{
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 0.1rem !important;
        }}
        .eb-dish-head-row [data-testid="column"]:last-child {{
            flex: 0 0 2.2rem !important;
            width: 2.2rem !important;
            min-width: 2.2rem !important;
            max-width: 2.2rem !important;
        }}
        .eb-dish-header-row {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: space-between !important;
            gap: 0.15rem !important;
            width: 100% !important;
            margin-bottom: 0.25rem !important;
        }}
        .eb-dish-header-row .eb-dish-name {{
            flex: 1 1 auto !important;
            min-width: 0 !important;
            margin: 0 !important;
        }}
        .eb-heart-wrap {{
            flex: 0 0 auto !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        .eb-heart-wrap .stButton {{
            margin: 0 !important;
            padding: 0 !important;
        }}
        .eb-heart-wrap .stButton > button {{
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 0.1rem !important;
            margin: 0 !important;
            min-height: unset !important;
            height: auto !important;
            font-size: 1.35rem !important;
            line-height: 1 !important;
        }}
        div[data-testid="stRadio"] > div {{
            flex-wrap: nowrap !important;
            display: flex !important;
            flex-direction: row !important;
            width: 100% !important;
            gap: 0 !important;
            justify-content: space-between !important;
        }}
        .eb-evening-review div[data-testid="stRadio"] label {{
            flex: 1 1 0 !important;
            min-width: 0 !important;
            max-width: none !important;
            padding: 0.28rem 0 !important;
            margin: 0 !important;
            justify-content: center !important;
            font-size: 0.82rem !important;
        }}
        .eb-evening-review div[data-testid="stRadio"] label span {{
            font-size: 0.82rem !important;
        }}
        .eb-evening-review div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] {{
            display: none !important;
        }}
        .eb-morning-block [data-testid="stWidgetLabel"] {{
            display: none !important;
        }}
        .eb-morning-block .eb-morning-q-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: #1E293B;
            margin: 0.5rem 0 0.25rem;
            white-space: nowrap;
        }}
        .eb-morning-block div[data-testid="stRadio"] > div {{
            flex-wrap: nowrap !important;
        }}
        .eb-morning-block div[data-testid="stRadio"] label {{
            flex: 1 1 auto !important;
            max-width: none !important;
            white-space: nowrap !important;
            word-break: keep-all !important;
            padding: 0.35rem 0.25rem !important;
        }}
        .eb-dish-meta {{
            font-size: 1rem;
            color: #64748B;
            margin: 0.15rem 0 0.5rem;
        }}
        .eb-score-label {{
            font-family: 'Noto Serif SC', serif;
            font-size: 1.05rem;
            font-weight: 600;
            color: #1E293B;
            margin: 0.35rem 0 0.15rem;
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


def _render_morning_section(today_iso: str) -> None:
    section_title("fa-sun", "晨间三问")
    st.caption(morning_greeting())
    st.markdown('<div class="eb-morning-block">', unsafe_allow_html=True)

    st.markdown('<p class="eb-morning-q-title">一、昨晚睡眠状态</p>', unsafe_allow_html=True)
    sleep = st.radio(
        "昨晚睡眠状态",
        SLEEP_OPTIONS,
        horizontal=True,
        label_visibility="collapsed",
        key="morning_sleep",
    )

    st.markdown('<p class="eb-morning-q-title">二、今日脑力/体力消耗</p>', unsafe_allow_html=True)
    load = st.radio(
        "脑力体力消耗",
        LOAD_OPTIONS,
        horizontal=True,
        label_visibility="collapsed",
        key="morning_load",
    )

    st.markdown('<p class="eb-morning-q-title">三、今日一人食餐数</p>', unsafe_allow_html=True)
    meal_count = st.radio(
        "一人食餐数",
        MEAL_COUNT_OPTIONS,
        horizontal=True,
        label_visibility="collapsed",
        key="morning_meal_count",
        format_func=lambda x: f"{x} 餐",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("保存晨间记录", type="secondary", use_container_width=True, key="save_morning_context"):
        save_morning_context(today_iso, sleep, load, int(meal_count))
        st.session_state.morning_inputs = {
            "sleep": sleep,
            "load": load,
            "meal_count": int(meal_count),
        }
        st.session_state.morning_context_loaded = today_iso
        st.session_state.record_saved_flash = True
        st.rerun()

    if st.session_state.pop("record_saved_flash", False):
        st.success("晨间记录已保存 · 可前往「菜单」生成今日餐食。")


def _render_evening_section(confirmed: dict) -> None:
    menu_ids: list[str] = list(confirmed["menu_ids"])
    morning = st.session_state.get("morning_inputs", {})
    today = confirmed["date"]

    section_title("fa-utensils", "今日餐食评价")

    st.markdown('<div class="eb-evening-review">', unsafe_allow_html=True)
    for menu_id in menu_ids:
        menu_row = get_menu_by_id(menu_id)
        if not menu_row:
            continue

        with st.container(border=True):
            meal_type = str(menu_row.get("meal_type", "")).strip()
            dish_name = menu_row["menu_name"]
            st.markdown('<div class="eb-dish-head-row">', unsafe_allow_html=True)
            title_col, heart_col = st.columns([9, 1], gap="small")
            with title_col:
                st.markdown(
                    f'<p class="eb-dish-name">{meal_type}：{dish_name}</p>',
                    unsafe_allow_html=True,
                )
            with heart_col:
                render_dish_favorite_heart(menu_id)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<p class="eb-score-label">操作从容度 (1-5分)</p>', unsafe_allow_html=True)
            st.caption("1分：极其匆忙 → 5分：优雅享受")
            st.radio(
                "操作从容度",
                options=SCORE_OPTIONS,
                horizontal=True,
                format_func=_score_btn,
                label_visibility="collapsed",
                key=f"review_{menu_id}_operation",
                index=None,
            )

            st.markdown(
                '<p class="eb-score-label">这道菜我还想再吃一次 (1-5分)</p>',
                unsafe_allow_html=True,
            )
            st.caption("1分：极不赞成 → 5分：极度赞成")
            st.radio(
                "NPS意愿",
                options=SCORE_OPTIONS,
                horizontal=True,
                format_func=_score_btn,
                label_visibility="collapsed",
                key=f"review_{menu_id}_nps",
                index=None,
            )

    st.checkbox("🌟 收藏今日整套全天菜单", key="review_fav_full_day")

    section_title("fa-heart-pulse", "全天个人状态")

    st.markdown("**情绪状态 (1-5分)**")
    st.caption("1分：很低落 → 5分：很愉悦")
    day_mood = st.radio(
        "情绪状态",
        options=SCORE_OPTIONS,
        horizontal=True,
        format_func=_score_btn,
        label_visibility="collapsed",
        key="review_day_mood",
        index=None,
    )

    st.markdown("**精力水平 (1-5分)**")
    st.caption("1分：很疲惫 → 5分：精力充沛")
    day_energy = st.radio(
        "精力水平",
        options=SCORE_OPTIONS,
        horizontal=True,
        format_func=_score_btn,
        label_visibility="collapsed",
        key="review_day_energy",
        index=None,
    )

    if st.button("完成今日回顾，去生成日志", type="primary", use_container_width=True, key="review_submit"):
        if not _review_scores_complete(menu_ids):
            st.warning("请完成所有评分后再提交。")
            return
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

        recalculate_weights()
        st.session_state.last_log_id = log_ids[-1] if log_ids else None
        st.session_state.review_complete = True
        st.session_state.current_page = "export"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f'<p class="eb-ritual">{_ritual_line()}</p>',
        unsafe_allow_html=True,
    )


def render() -> None:
    init_database()
    hydrate_today_state()
    _inject_review_card_css()

    today_iso = st.session_state.get("today_date", date.today().isoformat())
    _render_morning_section(today_iso)

    confirmed = get_confirmed_plan(today_iso)
    if not confirmed:
        st.warning("请先在「菜单」页确认今日就餐计划，再填写下方晚间回顾。")
        return

    st.divider()
    section_title("fa-moon", "晚间回顾")
    st.caption("以下为您在「今日菜单」中已确认的就餐计划。")
    _render_evening_section(confirmed)
