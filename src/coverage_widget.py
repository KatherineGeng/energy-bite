"""Nutrition coverage — inline summary + compact popover trigger."""

from __future__ import annotations

import streamlit as st

from src.nutrition import (
    covered_categories,
    coverage_detail_rows,
    coverage_summary,
)


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


def _render_coverage_inline(menu_row: dict, *, line: str) -> None:
    """Meta text with popover button immediately after on the same row."""
    meta_col, pop_col = st.columns([8, 2], gap="small")
    with meta_col:
        st.markdown(f'<span class="eb-meal-meta-inline">{line}</span>', unsafe_allow_html=True)
    with pop_col:
        with st.popover("点击查看"):
            _render_coverage_detail(menu_row)


def render_coverage_badge(menu_row: dict, key: str) -> None:
    del key
    summary = coverage_summary(menu_row)
    _render_coverage_inline(menu_row, line=f"营养覆盖 {summary}")


def render_meal_headline(
    meal_type: str,
    row: dict,
    *,
    idx: int,
    locked: bool,
    widget_key: str,
    ai_fresh: bool = False,
) -> None:
    del locked, widget_key
    tags_str = str(row.get("energy_tags", "")).replace("·", " · ")
    summary = coverage_summary(row)
    ai_tag = " · `AI新菜`" if ai_fresh else ""
    prep = f"⏱ {row['prep_minutes']} min · "

    if idx == 0:
        st.markdown(f"**{meal_type}** · **{row['menu_name']}**{ai_tag}")
    else:
        st.markdown(f"· **{row['menu_name']}**{ai_tag}")

    _render_coverage_inline(row, line=f"{tags_str} · {prep}营养覆盖 {summary}")
