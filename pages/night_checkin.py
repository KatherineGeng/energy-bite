"""晚间回顾 — 简愈一人食 V4.0."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.algorithm import recalculate_weights
from src.database import (
    append_log,
    get_menu_by_id,
    init_database,
    save_favorite_dish,
    save_favorite_menu_set,
)
from src.theme import ACCENT, page_title, section_title

SCORE_OPTIONS = [1, 2, 3, 4, 5]
OPERATION_LABELS = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5"}
NPS_LABELS = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5"}


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
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0;
            color: #1E293B;
        }}
        .eb-dish-meta {{
            font-size: 0.82rem;
            color: #64748B;
            margin: 0.15rem 0 0.5rem;
        }}
        .eb-score-label {{
            font-family: 'Noto Serif SC', serif;
            font-size: 0.92rem;
            font-weight: 600;
            color: #1E293B;
            margin: 0.35rem 0 0.15rem;
        }}
        .eb-ritual {{
            text-align: center;
            font-size: 0.95rem;
            color: {ACCENT};
            font-family: 'Noto Serif SC', serif;
            margin: 0.75rem 0 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    init_database()
    _inject_review_card_css()

    page_title("fa-leaf", "晚间回顾", "逐道回顾今日餐食，再回望全天身心状态。")

    if not st.session_state.get("menu_locked") or not st.session_state.get("final_daily_list"):
        st.warning("请先前往【晨间餐饮】确认今日计划，再回来回顾。")
        return

    menu_ids: list[str] = list(st.session_state.final_daily_list)
    morning = st.session_state.get("morning_inputs", {})
    today = st.session_state.get("today_date", date.today().isoformat())

    section_title("fa-utensils", "今日餐食评价")

    for menu_id in menu_ids:
        menu_row = get_menu_by_id(menu_id)
        if not menu_row:
            continue

        with st.container(border=True):
            st.markdown(
                f'<p class="eb-dish-name">{menu_row["menu_name"]}</p>'
                f'<p class="eb-dish-meta">{menu_row.get("meal_type", "")}</p>',
                unsafe_allow_html=True,
            )

            st.markdown('<p class="eb-score-label">操作从容度 (1-5)</p>', unsafe_allow_html=True)
            st.caption("1极其匆忙 → 5优雅享受")
            st.radio(
                "操作从容度",
                options=SCORE_OPTIONS,
                horizontal=True,
                format_func=lambda x: OPERATION_LABELS[x],
                label_visibility="collapsed",
                key=f"review_{menu_id}_operation",
                index=2,
            )

            st.markdown(
                '<p class="eb-score-label">NPS意愿：这道菜我还想再吃一次 (1-5)</p>',
                unsafe_allow_html=True,
            )
            st.caption("1极不赞成 → 5极度赞成")
            st.radio(
                "NPS意愿",
                options=SCORE_OPTIONS,
                horizontal=True,
                format_func=lambda x: NPS_LABELS[x],
                label_visibility="collapsed",
                key=f"review_{menu_id}_nps",
                index=3,
            )

            st.checkbox("❤️ 收藏这道菜品", key=f"review_{menu_id}_fav_dish")

    st.checkbox("🌟 收藏今日整套全天菜单", key="review_fav_full_day")

    section_title("fa-heart-pulse", "全天个人状态")

    mood_col, energy_col = st.columns(2)
    with mood_col:
        st.markdown("**情绪状态 (1-5)**")
        day_mood = st.radio(
            "情绪状态",
            options=SCORE_OPTIONS,
            horizontal=True,
            label_visibility="collapsed",
            key="review_day_mood",
            index=2,
        )
    with energy_col:
        st.markdown("**精力水平 (1-5)**")
        day_energy = st.radio(
            "精力水平",
            options=SCORE_OPTIONS,
            horizontal=True,
            label_visibility="collapsed",
            key="review_day_energy",
            index=2,
        )

    if st.button("完成今日回顾，去生成日志", type="primary", use_container_width=True, key="review_submit"):
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

    st.markdown(
        '<p class="eb-ritual">我度过了快乐健康的一天</p>',
        unsafe_allow_html=True,
    )
