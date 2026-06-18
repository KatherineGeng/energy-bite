"""Nutrition category coverage for menus."""

from __future__ import annotations

from src.constants import NUTRITION_ALIAS, NUTRITION_CATEGORIES
from src.database import get_ingredient_map, parse_list_field


def _normalize_category(raw: str) -> str | None:
    text = raw.strip()
    if text in NUTRITION_CATEGORIES:
        return text
    return NUTRITION_ALIAS.get(text)


def nutrition_coverage_for_menu(menu_row: dict) -> dict[str, float]:
    """
    Return coverage ratio per canonical category (0.0–1.0).
    A category is covered (1.0) if at least one ingredient maps to it.
    """
    ingredient_map = get_ingredient_map()
    ids = parse_list_field(menu_row.get("ingredient_ids", ""))

    covered: set[str] = set()
    for ing_id in ids:
        ing = ingredient_map.get(ing_id)
        if not ing:
            continue
        for raw_cat in parse_list_field(ing.get("nutrition_category", ""), seps="|,"):
            canonical = _normalize_category(raw_cat)
            if canonical:
                covered.add(canonical)

    return {cat: (1.0 if cat in covered else 0.0) for cat in NUTRITION_CATEGORIES}


def coverage_summary(menu_row: dict) -> str:
    coverage = nutrition_coverage_for_menu(menu_row)
    hit = [cat for cat, val in coverage.items() if val > 0]
    return f"{len(hit)}/{len(NUTRITION_CATEGORIES)} 类"
