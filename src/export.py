"""Poster export facade — delegates to visualization V2 engine."""

from __future__ import annotations

from typing import Any

from src.visualization import generate_daily_poster, meals_for_poster_from_ids

__all__ = ["generate_daily_poster", "meals_for_poster_from_ids", "generate_poster"]


def generate_poster(
    date_str: str,
    meals: list[dict] | None = None,
    menu_ids: list[str] | None = None,
    photos: list[Any] | None = None,
    theme: str = "",
) -> bytes:
    if meals is None:
        meals = meals_for_poster_from_ids(menu_ids or [])
    return generate_daily_poster(date_str=date_str, meals=meals, photos=photos, theme=theme)
