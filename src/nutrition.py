"""Nutrition category coverage for menus."""

from __future__ import annotations

import html

from src.constants import NUTRITION_ALIAS, NUTRITION_CATEGORIES
from src.database import get_ingredient_map, parse_list_field
from src.nutrition_api import parse_nutrition_from_description


def _normalize_category(raw: str) -> str | None:
    text = raw.strip()
    if text in NUTRITION_CATEGORIES:
        return text
    return NUTRITION_ALIAS.get(text)


def nutrition_coverage_for_menu(menu_row: dict) -> dict[str, float]:
    """
    Return coverage ratio per canonical category (0.0–1.0).
    Merges ingredient-library mapping with stored |NUTR: categories (from API).
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

    _, stored_cats = parse_nutrition_from_description(str(menu_row.get("description", "")))
    covered.update(stored_cats)

    override = menu_row.get("_coverage_categories")
    if override:
        covered.update(c for c in override if c in NUTRITION_CATEGORIES)

    return {cat: (1.0 if cat in covered else 0.0) for cat in NUTRITION_CATEGORIES}


def coverage_summary(menu_row: dict) -> str:
    coverage = nutrition_coverage_for_menu(menu_row)
    hit = [cat for cat, val in coverage.items() if val > 0]
    return f"{len(hit)}/{len(NUTRITION_CATEGORIES)} 类"


def coverage_detail_rows(menu_row: dict) -> list[dict[str, str]]:
    coverage = nutrition_coverage_for_menu(menu_row)
    return [
        {"营养类别": cat, "覆盖": "✓" if coverage[cat] > 0 else "—"}
        for cat in NUTRITION_CATEGORIES
    ]


def covered_categories(menu_row: dict) -> list[str]:
    coverage = nutrition_coverage_for_menu(menu_row)
    return [cat for cat, val in coverage.items() if val > 0]


def coverage_inline_html(menu_row: dict) -> str:
    """Inline summary + (i) tooltip — table only visible on hover/focus."""
    summary = coverage_summary(menu_row)
    rows = coverage_detail_rows(menu_row)
    body = "".join(
        f"<tr><td>{html.escape(r['营养类别'])}</td>"
        f"<td class='eb-cov-mark'>{html.escape(r['覆盖'])}</td></tr>"
        for r in rows
    )
    hit = covered_categories(menu_row)
    foot = html.escape("已覆盖：" + "、".join(hit)) if hit else "尚未分析或未匹配营养类"

    tip_style = (
        "display:none!important;visibility:hidden!important;opacity:0!important;"
        "pointer-events:none!important;position:absolute;z-index:99999;right:0;top:calc(100% + 4px);"
        "min-width:11.5rem;max-width:16rem;padding:0.45rem 0.5rem;background:#fff;"
        "border:1px solid rgba(141,163,153,0.35);border-radius:10px;"
        "box-shadow:0 8px 24px rgba(30,41,59,0.12);font-size:0.72rem;font-weight:400;"
        "font-style:normal;color:#1E293B;text-align:left;white-space:normal;"
    )

    return (
        f'<span class="eb-cov-wrap">营养覆盖 {html.escape(summary)}'
        f'<sup class="eb-cov-i" tabindex="0" aria-label="查看营养覆盖">i</sup>'
        f'<span class="eb-cov-tip" role="tooltip" style="{tip_style}">'
        f"<strong>七大营养类覆盖</strong>"
        f"<table class='eb-cov-table'><thead><tr><th>类别</th><th>覆盖</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
        f"<span class='eb-cov-foot'>{foot}</span>"
        f"<span class='eb-cov-hint'>移开光标关闭 · 手机点 i 后点空白处关闭</span>"
        f"</span></span>"
    )


def menu_row_from_analysis(
    ingredients_text: str,
    analysis: dict,
    dish_name: str = "",
    prep_minutes: int = 15,
) -> dict:
    """Build a draft menu row dict for coverage badge preview."""
    from src.nutrition_api import encode_nutrition_description

    return {
        "menu_name": dish_name,
        "ingredient_ids": "|".join(analysis.get("ingredient_ids", [])),
        "description": encode_nutrition_description(
            ingredients_text, analysis.get("categories", [])
        ),
        "prep_minutes": prep_minutes,
        "energy_tags": analysis.get("energy_tags", "手工添加"),
        "_coverage_categories": analysis.get("categories", []),
    }
