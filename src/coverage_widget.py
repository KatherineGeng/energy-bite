"""Nutrition coverage — native Streamlit (mobile-safe, no iframes)."""

from __future__ import annotations

import streamlit as st

from src.nutrition import (
    covered_categories,
    coverage_detail_rows,
    coverage_summary,
)

ACCENT = "#8DA399"


def _render_coverage_detail(menu_row: dict) -> None:
    rows = coverage_detail_rows(menu_row)
    st.markdown("**七大营养类覆盖**")
    for row in rows:
        mark = row["覆盖"]
        st.markdown(f"- {row['营养类别']}：{mark}")
    hit = covered_categories(menu_row)
    if hit:
        st.caption("已覆盖：" + "、".join(hit))
    else:
        st.caption("尚未分析或未匹配营养类")


def render_coverage_badge(menu_row: dict, key: str) -> None:
    """Summary line + popover detail."""
    summary = coverage_summary(menu_row)
    col1, col2 = st.columns([5, 1])
    with col1:
        st.caption(f"营养覆盖 {summary}")
    with col2:
        with st.popover("i", use_container_width=True):
            _render_coverage_detail(menu_row)


def render_meal_headline(
    meal_type: str,
    row: dict,
    *,
    idx: int,
    locked: bool,
    widget_key: str,
    ai_fresh: bool = False,
) -> None:
    del widget_key  # kept for call-site compatibility
    tags_str = str(row.get("energy_tags", "")).replace("·", " · ")
    summary = coverage_summary(row)
    ai_tag = " · `AI新菜`" if ai_fresh else ""

    if idx == 0:
        st.markdown(f"**{meal_type}** · **{row['menu_name']}**{ai_tag}")
    else:
        st.markdown(f"· **{row['menu_name']}**{ai_tag}")

    if locked:
        meta = f"{tags_str} · 营养覆盖 {summary}"
    else:
        meta = f"{tags_str} · ⏱ {row['prep_minutes']} min · 营养覆盖 {summary}"

    meta_col, pop_col = st.columns([11, 1])
    with meta_col:
        st.caption(meta)
    with pop_col:
        with st.popover("i", use_container_width=True):
            _render_coverage_detail(row)
