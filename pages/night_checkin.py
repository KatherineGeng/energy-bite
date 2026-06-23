"""回顾页 — 晨间三问 + 晚间回顾."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.algorithm import recalculate_weights
from src.constants import LOAD_OPTIONS, MEAL_COUNT_OPTIONS, SLEEP_OPTIONS
from src.database import (
    append_log,
    get_menu_row,
    load_favorites_dishes,
    remove_favorite_dish,
    save_favorite_dish,
    save_favorite_menu_set,
    save_morning_context,
)
from src.review_ui import render_dish_header_with_favorite, render_score_picker
from src.session_hydrate import get_confirmed_plan
from src.theme import ACCENT, section_title
from src.user_profile import morning_greeting, nickname

SCORE_OPTIONS = [1, 2, 3, 4, 5]


def _score_btn(x: int) -> str:
    return str(x)


def _toggle_dish_favorite(menu_id: str, today: str) -> None:
    key = f"review_{menu_id}_fav_dish"
    st.session_state[key] = not bool(st.session_state.get(key, False))
    if st.session_state[key]:
        save_favorite_dish(menu_id, today)
        st.toast("已收藏此菜品", icon="❤️")
    else:
        remove_favorite_dish(menu_id, today)
        st.toast("已取消收藏")


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
        .eb-dish-header-line {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            justify-content: space-between !important;
            gap: 0.35rem !important;
            width: 100% !important;
            margin: 0 0 0.35rem !important;
        }}
        .eb-dish-header-line .eb-dish-name {{
            flex: 1 1 auto !important;
            min-width: 0 !important;
            margin: 0 !important;
        }}
        a.eb-fav-link {{
            flex: 0 0 auto !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 0.12rem !important;
            text-decoration: none !important;
            color: #64748B !important;
            font-size: 0.92rem !important;
            white-space: nowrap !important;
            -webkit-tap-highlight-color: transparent;
        }}
        a.eb-fav-link.active {{
            color: #EF4444 !important;
        }}
        .eb-fav-heart {{
            font-size: 1.05rem !important;
            line-height: 1 !important;
        }}
        .eb-score-pick-row button {{
            min-height: 2.15rem !important;
            padding: 0.25rem 0 !important;
            font-size: 0.88rem !important;
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
    snapshots = confirmed.get("snapshots", {})
    _hydrate_review_favorites(menu_ids, today)
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
                on_toggle=lambda m=menu_id, d=today: _toggle_dish_favorite(m, d),
            )

            render_score_picker(
                "操作从容度 (1-5分)",
                "1：极其匆忙 → 5：优雅享受",
                f"review_{menu_id}_operation",
                btn_prefix=f"review_{menu_id}_op",
            )
            render_score_picker(
                "这道菜我还想再吃一次 (1-5分)",
                "1：极不赞成 → 5：极度赞成",
                f"review_{menu_id}_nps",
                btn_prefix=f"review_{menu_id}_nps",
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
    today_iso = st.session_state.get("today_date", date.today().isoformat())
    _inject_review_card_css()

    confirmed = get_confirmed_plan(today_iso)
    if confirmed:
        section_title("fa-moon", "晚间回顾")
        st.caption("以下为您在「今日菜单」中已确认的就餐计划。")
        _render_evening_section(confirmed)
        st.divider()
        with st.expander("晨间三问（可选）", expanded=False):
            _render_morning_section(today_iso)
        return

    _render_morning_section(today_iso)
    st.warning("请先在「菜单」页确认今日就餐计划，再填写晚间回顾。")
