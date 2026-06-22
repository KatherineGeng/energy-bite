"""AI-powered daily menu generation (after library quota exhausted)."""

from __future__ import annotations

import json
import random
import re
import urllib.error
from typing import Any

import pandas as pd

from src.constants import LOAD_TAG_BOOST, NUTRITION_CATEGORIES, SLEEP_TAG_BOOST
from src.database import append_manual_menu, load_menus
from src.llm_client import call_json, has_api_key
from src.nutrition_api import analyze_ingredients
from src.recommendation import _meal_type_for_count


def _menu_catalog_text(exclude: set[str]) -> str:
    menus = load_menus()
    if menus.empty:
        return ""
    lines: list[str] = []
    for _, row in menus.iterrows():
        mid = str(row["menu_id"])
        if mid in exclude:
            continue
        lines.append(
            f"{mid}|{row['meal_type']}|{row['menu_name']}|"
            f"{row.get('energy_tags', '')}|{row.get('prep_minutes', '')}min"
        )
    return "\n".join(lines)


def _existing_menu_names() -> set[str]:
    menus = load_menus()
    if menus.empty:
        return set()
    return set(menus["menu_name"].astype(str).str.strip().tolist())


def _normalize_raw_response(raw: dict[str, Any]) -> dict[str, Any]:
    if "picks" not in raw:
        if "menus" in raw:
            raw["picks"] = raw["menus"]
        elif "recommendations" in raw:
            raw["picks"] = raw["recommendations"]
    if "new_menus" not in raw:
        if "new_dishes" in raw:
            raw["new_menus"] = raw["new_dishes"]
        elif "dishes" in raw:
            raw["new_menus"] = raw["dishes"]
    return raw


def _resolve_menu_id(mid: str, menus: pd.DataFrame) -> str | None:
    text = str(mid).strip()
    if not text:
        return None

    ids = set(menus["menu_id"].astype(str).tolist())
    upper = text.upper()
    if upper in ids:
        return upper

    match = re.match(r"^MENU[_-]?(\d+)$", upper)
    if match:
        candidate = f"MENU_{int(match.group(1)):03d}"
        if candidate in ids:
            return candidate

    if text.isdigit():
        candidate = f"MENU_{int(text):03d}"
        if candidate in ids:
            return candidate

    by_name = menus[menus["menu_name"].astype(str).str.strip() == text]
    if not by_name.empty:
        return str(by_name.iloc[0]["menu_id"])

    return None


def _order_by_slots(rows: list[dict], slots: list[str]) -> list[dict]:
    """Map created dishes to meal slots without library fallback."""
    by_slot: dict[str, dict] = {}
    leftovers: list[dict] = []
    for row in rows:
        slot = str(row.get("meal_type", ""))
        if slot in slots and slot not in by_slot:
            by_slot[slot] = row
        else:
            leftovers.append(row)
    for slot in slots:
        if slot in by_slot:
            continue
        if leftovers:
            candidate = leftovers.pop(0)
            by_slot[slot] = {**candidate, "meal_type": slot}
    return [by_slot[slot] for slot in slots if slot in by_slot]


def _assign_to_slots(
    rows: list[dict],
    slots: list[str],
    exclude_ids: set[str],
) -> list[dict]:
    menus = load_menus()
    by_slot: dict[str, dict] = {}
    leftovers: list[dict] = []
    used_ids: set[str] = set(exclude_ids)

    for row in rows:
        slot = str(row.get("meal_type", ""))
        mid = str(row.get("menu_id", ""))
        if not mid or mid in exclude_ids:
            continue
        if slot in slots and slot not in by_slot:
            by_slot[slot] = row
            used_ids.add(mid)
        else:
            leftovers.append(row)

    for slot in slots:
        if slot in by_slot:
            continue
        while leftovers:
            candidate = leftovers.pop(0)
            mid = str(candidate.get("menu_id", ""))
            if mid and mid not in used_ids:
                candidate = {**candidate, "meal_type": slot}
                by_slot[slot] = candidate
                used_ids.add(mid)
                break

    for slot in slots:
        if slot in by_slot:
            continue
        subset = menus[
            (menus["meal_type"] == slot) & (~menus["menu_id"].astype(str).isin(used_ids))
        ]
        if subset.empty:
            subset = menus[menus["meal_type"] == slot]
        if subset.empty:
            subset = menus[~menus["menu_id"].astype(str).isin(used_ids)]
        if subset.empty:
            subset = menus
        if subset.empty:
            continue
        picked = subset.sample(1, random_state=random.randint(0, 2**31 - 1)).iloc[0].to_dict()
        by_slot[slot] = picked
        used_ids.add(str(picked["menu_id"]))

    return [by_slot[slot] for slot in slots if slot in by_slot]


def _create_ai_dish(item: dict[str, Any], existing_names: set[str]) -> dict | None:
    """Create one AI dish, analyze nutrition via API, append to menu_db."""
    name = str(item.get("menu_name", "")).strip()
    ing = str(item.get("ingredients_text", "")).strip()
    if not name or not ing or name in existing_names:
        return None

    slot = str(item.get("meal_type", "午餐"))
    prep = int(item.get("prep_minutes") or 15)
    tags = str(item.get("energy_tags", "AI推荐"))

    analysis = analyze_ingredients(ing)
    cats = analysis.get("categories") or [
        c for c in item.get("categories", []) if c in NUTRITION_CATEGORIES
    ]
    ing_ids = analysis.get("ingredient_ids") or []

    mid = append_manual_menu(
        name,
        prep_minutes=prep,
        ingredients_text=ing,
        ingredient_ids=ing_ids,
        energy_tags=tags,
        meal_type=slot,
        nutrition_categories=cats,
        description="AI创作",
    )
    fresh = load_menus()
    match = fresh[fresh["menu_id"] == mid]
    if match.empty:
        return None
    row = match.iloc[0].to_dict()
    row["_ai_created"] = True
    existing_names.add(name)
    return row


def _fresh_menu_prompt(
    sleep_quality: str,
    brain_body_load: str,
    meal_count: int,
    slots_text: str,
    sleep_tags: str,
    load_tags: str,
    catalog: str,
    cats: str,
    exclude_text: str,
    *,
    strict: bool = False,
) -> str:
    strict_line = (
        "\n7. 再次强调：picks 必须是空数组 []，禁止从菜品库选菜。"
        if strict
        else ""
    )
    return f"""为「简愈一人食」用户创作今日全新一人食菜单（第 4 次及以上个性化推荐）。

晨间状态：
- 睡眠：{sleep_quality}（偏好标签：{sleep_tags}）
- 消耗：{brain_body_load}（偏好标签：{load_tags}）
- 餐数：{meal_count}（需覆盖餐次：{slots_text}）
- 今日已用过的菜品（菜名勿重复）：{exclude_text}

菜品库仅供参考风格，本次禁止直接选用（picks 必须为空）：
{catalog}

七大营养类：{cats}

请返回 JSON：
{{
  "picks": [],
  "new_menus": [
    {{
      "menu_name": "独创菜名（不得与菜品库已有菜名相同）",
      "meal_type": "早餐",
      "ingredients_text": "具体食材1、食材2、食材3",
      "prep_minutes": 15,
      "energy_tags": "稳糖·快速供能",
      "categories": ["蛋白质", "膳食纤维"]
    }}
  ],
  "note": "一句中文推荐理由"
}}

规则：
1. picks 必须为空数组 []，不得从菜品库选 menu_id。
2. new_menus 必须恰好 {meal_count} 道，meal_type 覆盖 {slots_text} 各一道。
3. 每道菜须有具体中文菜名、详细食材清单（顿号分隔）、准备分钟数、1-3 个能量标签。
4. categories 只能从七大营养类中选，每道菜至少 2 类。
5. 根据晨间状态个性化设计，体现抗炎/稳糖/补脑等取向。
6. 只输出 JSON，不要 markdown 代码块。{strict_line}"""


def suggest_daily_menus_api(
    sleep_quality: str,
    brain_body_load: str,
    meal_count: int,
    exclude_menu_ids: list[str] | None = None,
    *,
    shuffle: bool = False,
) -> tuple[pd.DataFrame | None, str, list[str]]:
    """
    Ask DeepSeek to create brand-new dishes (4th+ generation).
    Returns (menus DataFrame, note, new_menu_ids) or (None, error, []).
    """
    del shuffle  # fresh mode always creates new dishes
    if not has_api_key():
        return None, "未配置 DEEPSEEK_API_KEY。", []

    exclude = set(str(x) for x in (exclude_menu_ids or []))
    slots = _meal_type_for_count(meal_count)
    slots_text = "、".join(slots)
    sleep_tags = "、".join(SLEEP_TAG_BOOST.get(sleep_quality, []))
    load_tags = "、".join(LOAD_TAG_BOOST.get(brain_body_load, []))
    catalog = _menu_catalog_text(exclude)
    cats = "、".join(NUTRITION_CATEGORIES)

    menus = load_menus()
    exclude_names = set()
    if not menus.empty and exclude:
        exclude_names = set(
            menus[menus["menu_id"].astype(str).isin(exclude)]["menu_name"].astype(str).tolist()
        )
    exclude_text = "、".join(sorted(exclude_names)) if exclude_names else "无"

    for strict in (False, True):
        prompt = _fresh_menu_prompt(
            sleep_quality,
            brain_body_load,
            meal_count,
            slots_text,
            sleep_tags,
            load_tags,
            catalog,
            cats,
            exclude_text,
            strict=strict,
        )
        try:
            raw = call_json(
                prompt,
                system_prompt=(
                    "你是简愈一人食菜单创作助手。"
                    "用户第4次及以上生成时必须创作全新菜品，只输出 JSON。"
                ),
            )
            raw = _normalize_raw_response(raw)
            result = _build_fresh_dataframe(raw, meal_count)
            if result[0] is not None:
                return result
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            KeyError,
            IndexError,
            ValueError,
        ) as exc:
            return None, f"AI 菜单生成失败：{exc}", []

    return None, "AI 未返回足够的新菜品（需全部使用 new_menus 创作）。", []


def _build_fresh_dataframe(
    raw: dict[str, Any],
    meal_count: int,
) -> tuple[pd.DataFrame | None, str, list[str]]:
    """Only accept AI-created new_menus; analyze nutrition and write to menu_db."""
    slots = _meal_type_for_count(meal_count)
    ai_note = str(raw.get("note", "已由 AI 创作今日菜单。"))
    existing_names = _existing_menu_names()
    rows: list[dict] = []
    new_ids: list[str] = []

    for item in raw.get("new_menus", []):
        row = _create_ai_dish(item, existing_names)
        if row:
            rows.append(row)
            new_ids.append(str(row["menu_id"]))

    assigned = _order_by_slots(rows, slots)
    if len(assigned) < meal_count:
        return None, "AI 返回的新菜品数量不足。", []

    names = "、".join(str(r.get("menu_name", "")) for r in assigned[:meal_count])
    note = f"{ai_note} 已创作 {len(assigned[:meal_count])} 道新菜：{names}。"
    return pd.DataFrame(assigned[:meal_count]), note, new_ids
