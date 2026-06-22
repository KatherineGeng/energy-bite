"""Meal plan date metadata for calendar markers."""

from __future__ import annotations

from src.database import DAILY_PLAN_COLUMNS, _parse_plan_column, _read_csv, archive_date_markers
from src.constants import DAILY_PLAN_FILE


def meal_plan_date_markers(user_key: str = "") -> dict[str, str]:
    """Return {iso_date: status} for dates that have saved menus (optionally scoped by user)."""
    df = _read_csv(DAILY_PLAN_FILE, DAILY_PLAN_COLUMNS)
    markers: dict[str, str] = {}
    uk = str(user_key or "").strip()

    if not df.empty:
        for _, row in df.iterrows():
            day = str(row.get("date", "")).strip()
            if not day:
                continue
            row_uk = str(row.get("user_key", "")).strip()
            if uk and row_uk and row_uk != uk:
                continue
            ids = (
                _parse_plan_column(row.get("breakfast", ""))
                + _parse_plan_column(row.get("lunch", ""))
                + _parse_plan_column(row.get("dinner", ""))
            )
            if not ids:
                continue
            confirmed = str(row.get("confirmed", "")).lower() in ("true", "1", "yes")
            markers[day] = "confirmed" if confirmed else "draft"

    for day, status in archive_date_markers().items():
        if day not in markers:
            markers[day] = status

    return markers


def markers_with_today(
    today_iso: str,
    *,
    today_has_menu: bool,
    today_confirmed: bool,
    user_key: str = "",
) -> dict[str, str]:
    markers = meal_plan_date_markers(user_key)
    if today_has_menu:
        markers[today_iso] = "confirmed" if today_confirmed else "draft"
    return markers
