"""Recommend full-day menus from recent favorites."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.database import load_favorites_menus


def _menu_ids_key(menu_ids: list[str]) -> tuple[str, ...]:
    return tuple(sorted(x.strip() for x in menu_ids if x.strip()))


def recent_favorite_menu_candidates(
    *,
    within_days: int = 5,
    exclude_menu_ids: list[str] | None = None,
    as_of: date | None = None,
) -> list[dict[str, Any]]:
    """
    Favorite full-day menus within the last N days, newest first.
    Skips sets identical to exclude_menu_ids (e.g. today's confirmed menu).
    """
    today = as_of or date.today()
    cutoff = (today - timedelta(days=within_days)).isoformat()
    exclude_key = _menu_ids_key(exclude_menu_ids or [])

    favs = load_favorites_menus()
    if favs.empty:
        return []

    out: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, ...]] = set()
    for _, row in favs.sort_values("date", ascending=False).iterrows():
        day = str(row.get("date", "")).strip()
        if not day or day < cutoff or day > today.isoformat():
            continue
        mids = [x.strip() for x in str(row.get("menu_ids", "")).split("|") if x.strip()]
        if len(mids) < 2:
            continue
        key = _menu_ids_key(mids)
        if not key or key in seen_keys:
            continue
        if exclude_key and key == exclude_key:
            continue
        seen_keys.add(key)
        out.append(
            {
                "date": day,
                "menu_ids": list(mids),
                "saved_at": str(row.get("saved_at", "")),
            }
        )
    return out
