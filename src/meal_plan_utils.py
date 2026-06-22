"""Meal plan helpers shared across pages."""

from __future__ import annotations

MEAL_ORDER = ["早餐", "午餐", "晚餐"]


def empty_meal_plan() -> dict[str, list[str]]:
    return {meal: [] for meal in MEAL_ORDER}


def active_meal_slots(meal_count: int) -> list[str]:
    if meal_count == 1:
        return ["午餐"]
    if meal_count == 2:
        return ["早餐", "晚餐"]
    return MEAL_ORDER.copy()


def flatten_plan(plan: dict[str, list[str]]) -> list[str]:
    ids: list[str] = []
    for meal in MEAL_ORDER:
        ids.extend(plan.get(meal, []))
    return ids


def plan_from_menu_ids(menu_ids: list[str], get_menu_by_id) -> dict[str, list[str]]:
    plan = empty_meal_plan()
    for menu_id in menu_ids:
        row = get_menu_by_id(menu_id)
        slot = row.get("meal_type", "午餐") if row else "午餐"
        if slot not in plan:
            slot = "午餐"
        plan[slot].append(menu_id)
    return plan
