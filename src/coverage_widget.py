"""Nutrition coverage — daily table + compact meal headlines."""

from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st

from src.constants import NUTRITION_CATEGORIES
from src.nutrition import (
    meal_slot_coverage_summary,
    nutrition_coverage_for_meal_slot,
)


def render_daily_coverage_table(
    plan: dict[str, list[str]],
    meal_slots: list[str],
    get_menu_by_id: Callable[[str], dict | None],
) -> None:
    """One table: rows = nutrition categories, columns = meal slots + daily total."""
    slot_rows: dict[str, list[dict]] = {}
    for meal in meal_slots:
        menu_ids = plan.get(meal, [])
        slot_rows[meal] = [
            row for mid in menu_ids if (row := get_menu_by_id(mid))
        ]

    summaries = [
        f"{meal} {meal_slot_coverage_summary(slot_rows[meal])}"
        for meal in meal_slots
    ]
    st.markdown("**今日营养覆盖 · 三餐一览**")
    st.caption(" · ".join(summaries))

    table_rows: list[dict[str, str]] = []
    for cat in NUTRITION_CATEGORIES:
        row: dict[str, str] = {"营养类别": cat}
        day_hit = False
        for meal in meal_slots:
            cov = nutrition_coverage_for_meal_slot(slot_rows[meal])
            hit = cov[cat] > 0
            row[meal] = "✓" if hit else "—"
            day_hit = day_hit or hit
        row["全天"] = "✓" if day_hit else "—"
        table_rows.append(row)

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


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
    ai_tag = " · `AI新菜`" if ai_fresh else ""
    prep = f"⏱ {row['prep_minutes']} min"

    if idx == 0:
        st.markdown(f"**{meal_type}** · **{row['menu_name']}**{ai_tag}")
    else:
        st.markdown(f"· **{row['menu_name']}**{ai_tag}")

    st.markdown(
        f'<span class="eb-meal-meta-inline">{tags_str} · {prep}</span>',
        unsafe_allow_html=True,
    )
