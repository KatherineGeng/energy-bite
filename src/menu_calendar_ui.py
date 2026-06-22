"""HTML month calendar — clickable dates with menus only."""

from __future__ import annotations

import calendar
from datetime import date
from urllib.parse import urlencode

import streamlit as st

from src.nav_params import append_nav_params


def _month_first(year: int, month: int) -> date:
    return date(year, month, 1)


def render_menu_calendar(
    marked_dates: set[str],
    selected: str,
    *,
    pick_key: str = "pick_date",
    month_key: str = "cal_month",
    extra_params: dict[str, str] | None = None,
) -> str:
    """
    Render calendar. Dates in marked_dates are dark & clickable; others gray.
    Returns currently selected ISO date.
    """
    extra = extra_params or {}
    today_iso = date.today().isoformat()

    month_str = st.query_params.get(month_key)
    if isinstance(month_str, list):
        month_str = month_str[0] if month_str else None

    if month_str and len(month_str) >= 7:
        try:
            y, m = month_str.split("-")[:2]
            view_year, view_month = int(y), int(m)
        except ValueError:
            base = date.fromisoformat(selected) if selected else date.today()
            view_year, view_month = base.year, base.month
    else:
        base = date.fromisoformat(selected) if selected else date.today()
        view_year, view_month = base.year, base.month

    picked = st.query_params.get(pick_key)
    if isinstance(picked, list):
        picked = picked[0] if picked else None
    if picked and picked in marked_dates:
        selected = picked
    elif selected not in marked_dates and marked_dates:
        selected = sorted(marked_dates, reverse=True)[0]

    def _link(params: dict[str, str]) -> str:
        merged = {**extra, **params}
        return append_nav_params("?" + urlencode(merged))

    prev_m = view_month - 1
    prev_y = view_year
    if prev_m < 1:
        prev_m, prev_y = 12, prev_y - 1
    next_m = view_month + 1
    next_y = view_year
    if next_m > 12:
        next_m, next_y = 1, next_y + 1

    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(view_year, view_month)

    day_cells: list[str] = []
    for week in weeks:
        for d in week:
            if d == 0:
                day_cells.append('<span class="eb-cal-day empty"></span>')
                continue
            iso = date(view_year, view_month, d).isoformat()
            if iso in marked_dates:
                cls = "eb-cal-day active"
                if iso == selected:
                    cls += " selected"
                if iso == today_iso:
                    cls += " today"
                href = _link({month_key: f"{view_year:04d}-{view_month:02d}", pick_key: iso})
                day_cells.append(f'<a class="{cls}" href="{href}">{d}</a>')
            else:
                cls = "eb-cal-day disabled"
                if iso == today_iso:
                    cls += " today"
                day_cells.append(f'<span class="{cls}">{d}</span>')

    grid = "".join(day_cells)
    html = f"""
    <div class="eb-cal">
      <div class="eb-cal-head">
        <a class="eb-cal-nav" href="{_link({month_key: f'{prev_y:04d}-{prev_m:02d}', pick_key: selected})}">‹</a>
        <span class="eb-cal-title">{view_year}年{view_month}月</span>
        <a class="eb-cal-nav" href="{_link({month_key: f'{next_y:04d}-{next_m:02d}', pick_key: selected})}">›</a>
      </div>
      <div class="eb-cal-weekdays">
        <span>日</span><span>一</span><span>二</span><span>三</span>
        <span>四</span><span>五</span><span>六</span>
      </div>
      <div class="eb-cal-grid">{grid}</div>
      <p class="eb-cal-hint">深色日期可点击查看菜单 · 灰色日期无记录</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    return selected
