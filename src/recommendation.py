"""Morning recommendation engine."""

from __future__ import annotations

import random

import pandas as pd

from src.constants import LOAD_TAG_BOOST, SLEEP_TAG_BOOST
from src.database import load_menus, load_weights, parse_energy_tags, parse_list_field


def _tag_match_score(menu_tags: list[str], boost_keywords: list[str]) -> float:
    if not menu_tags or not boost_keywords:
        return 0.0
    score = 0.0
    for tag in menu_tags:
        for keyword in boost_keywords:
            if keyword in tag or tag in keyword:
                score += 0.1
                break
    return score


def _meal_type_for_count(meal_count: int) -> list[str]:
    if meal_count == 1:
        return ["午餐"]
    if meal_count == 2:
        return ["早餐", "晚餐"]
    return ["早餐", "午餐", "晚餐"]


def _sort_key(row: pd.Series) -> tuple:
    favorited = bool(row.get("is_favorited", False))
    weight = float(row.get("sort_weight", 0.0))
    prep = int(row.get("prep_minutes", 999))
    return (0 if favorited else 1, -weight, prep)


def _build_scored_pool(
    sleep_quality: str,
    brain_body_load: str,
    meal_count: int,
) -> tuple[pd.DataFrame, list[str]]:
    menus = load_menus()
    if menus.empty:
        return menus, []

    weights = load_weights()
    weight_map: dict[str, float] = {}
    favorited_map: dict[str, bool] = {}
    if not weights.empty:
        for _, w in weights.iterrows():
            weight_map[w["menu_id"]] = float(w["final_weight"])
            favorited_map[w["menu_id"]] = bool(w["is_favorited"])

    boost_tags = SLEEP_TAG_BOOST.get(sleep_quality, []) + LOAD_TAG_BOOST.get(brain_body_load, [])

    rows = []
    for _, menu in menus.iterrows():
        tags = parse_energy_tags(menu["energy_tags"])
        base_weight = weight_map.get(menu["menu_id"], 0.0)
        if base_weight == 0.0:
            base_weight = 0.5
        tag_boost = _tag_match_score(tags, boost_tags)
        rows.append(
            {
                **menu.to_dict(),
                "is_favorited": favorited_map.get(menu["menu_id"], False),
                "sort_weight": base_weight + tag_boost,
                "parsed_tags": tags,
            }
        )

    result = pd.DataFrame(rows)
    preferred_types = _meal_type_for_count(meal_count)
    typed = result[result["meal_type"].isin(preferred_types)].copy()
    if typed.empty:
        typed = result.copy()
    return typed, preferred_types


def _pick_one(subset: pd.DataFrame, shuffle: bool, exclude_menu_ids: set[str]) -> pd.Series | None:
    if subset.empty:
        return None
    candidates = subset[~subset["menu_id"].isin(exclude_menu_ids)] if exclude_menu_ids else subset
    if candidates.empty:
        candidates = subset
    if shuffle:
        return candidates.sample(1, random_state=random.randint(0, 2**31 - 1)).iloc[0]
    ranked = candidates.copy()
    ranked["_sort"] = ranked.apply(_sort_key, axis=1)
    return ranked.sort_values("_sort").iloc[0]


def get_daily_menus(
    sleep_quality: str,
    brain_body_load: str,
    meal_count: int,
    shuffle: bool = False,
    exclude_menu_ids: list[str] | None = None,
) -> pd.DataFrame:
    typed, preferred_types = _build_scored_pool(sleep_quality, brain_body_load, meal_count)
    if typed.empty:
        return typed

    exclude = set(exclude_menu_ids or [])
    limit = min(meal_count, len(typed))

    if meal_count == 3:
        picked: list[pd.Series] = []
        used_ids: set[str] = set(exclude)
        for meal_type in preferred_types:
            subset = typed[typed["meal_type"] == meal_type]
            choice = _pick_one(subset, shuffle=shuffle, exclude_menu_ids=used_ids)
            if choice is not None:
                picked.append(choice)
                used_ids.add(choice["menu_id"])
        if len(picked) < 3:
            remaining = typed[~typed["menu_id"].isin({p["menu_id"] for p in picked} | used_ids)]
            for _, row in remaining.iterrows():
                if len(picked) >= 3:
                    break
                picked.append(row)
        return pd.DataFrame(picked) if picked else typed.head(limit)

    if shuffle:
        candidates = typed[~typed["menu_id"].isin(exclude)]
        if candidates.empty:
            candidates = typed
        return candidates.sample(min(limit, len(candidates)), random_state=random.randint(0, 2**31 - 1))

    ranked = typed.copy()
    ranked["_sort"] = ranked.apply(_sort_key, axis=1)
    return ranked.sort_values("_sort").drop(columns="_sort").head(limit)


def format_ingredient_names(menu_row: dict, ingredient_map: dict[str, dict]) -> str:
    ids = parse_list_field(menu_row.get("ingredient_ids", ""))
    names = []
    for ing_id in ids:
        ing = ingredient_map.get(ing_id)
        if ing:
            names.append(ing["name"])
    return "、".join(names) if names else "—"
