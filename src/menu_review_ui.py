"""Calendar menu review — shared by 我的 page."""

from __future__ import annotations

from datetime import date

import streamlit as st

from src.database import all_menu_ids_for_date, dates_with_menus, get_menu_by_id, get_menu_weight
from src.menu_calendar_ui import render_menu_calendar
from src.query_nav import qp_first
from src.session_hydrate import menu_ids_for_date
from src.share_code import encode_day_menu_share_text, encode_share_code


def _marked_dates_with_today() -> set[str]:
    marked = set(dates_with_menus())
    today_iso = st.session_state.get("today_date", date.today().isoformat())
    ids = menu_ids_for_date(today_iso)
    if not ids:
        ids = list(st.session_state.get("final_daily_list") or st.session_state.get("current_day_menus") or [])
    if ids:
        marked.add(today_iso)
    return marked


def render_menu_summary(date_str: str, menu_ids: list[str]) -> None:
    if not menu_ids:
        st.info(f"{date_str} 暂无已保存的菜单记录。")
        return
    for mid in menu_ids:
        row = get_menu_by_id(mid)
        if not row:
            continue
        st.markdown(f"**{row.get('meal_type', '')} · {row['menu_name']}**")
        st.caption(str(row.get("energy_tags", "")).replace("·", " · "))


def _menu_rows_for_ids(menu_ids: list[str]) -> list[dict]:
    rows: list[dict] = []
    for mid in menu_ids:
        row = get_menu_by_id(mid)
        if row:
            rows.append(row)
    return rows


def render_calendar_menu_review(*, nav_page: str = "mine", pick_key: str = "mine_date", month_key: str = "mine_month") -> None:
    marked = _marked_dates_with_today()
    today_iso = st.session_state.get("today_date", date.today().isoformat())

    if not marked:
        st.info("暂无历史菜单。在「菜单」页生成或确认就餐计划后会自动保存。")
        return

    pick_date = qp_first(pick_key) or st.session_state.get(pick_key) or today_iso
    if pick_date not in marked:
        pick_date = today_iso if today_iso in marked else sorted(marked, reverse=True)[0]

    pick_date = render_menu_calendar(
        marked,
        pick_date,
        pick_key=pick_key,
        month_key=month_key,
        extra_params={"nav": nav_page},
    )
    st.session_state[pick_key] = pick_date

    menu_ids = all_menu_ids_for_date(pick_date)
    if not menu_ids:
        menu_ids = menu_ids_for_date(pick_date)

    if not menu_ids:
        st.info(f"{pick_date} 暂无已保存的菜单记录。")
        return

    st.caption(f"{pick_date} 菜单")
    render_menu_summary(pick_date, menu_ids)

    rows = _menu_rows_for_ids(menu_ids)
    if not rows:
        return

    if st.button("生成当日分享口令", type="primary", use_container_width=True, key=f"{pick_key}_day_share"):
        st.session_state[f"{pick_key}_share_text"] = encode_day_menu_share_text(pick_date, rows)

    share_text = st.session_state.get(f"{pick_key}_share_text", "")
    if share_text:
        st.text_area(
            "分享口令（复制发送给好友）",
            value=share_text,
            height=140,
            key=f"{pick_key}_share_display",
        )

    with st.expander("单道菜口令", expanded=False):
        for row in rows:
            score = get_menu_weight(row["menu_id"])
            code = encode_share_code(
                ingredient_ids=row["ingredient_ids"],
                energy_tags=row["energy_tags"],
                estimated_score=score,
            )
            st.markdown(f"**{row.get('meal_type', '')} · {row['menu_name']}**")
            st.code(code, language=None)
