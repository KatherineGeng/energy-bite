"""Analyze free-text ingredients → seven nutrition categories (DeepSeek + fallback)."""

from __future__ import annotations

import json
import urllib.error
from typing import Any

from src.constants import NUTRITION_CATEGORIES
from src.database import load_ingredients, match_ingredients_from_text
from src.llm_client import api_key, call_json, has_api_key

NUTR_MARKER = "|NUTR:"


def parse_nutrition_from_description(description: str) -> tuple[str, list[str]]:
    text = str(description or "")
    if NUTR_MARKER not in text:
        return text, []
    base, cats_part = text.rsplit(NUTR_MARKER, 1)
    cats = [c.strip() for c in cats_part.split(",") if c.strip() in NUTRITION_CATEGORIES]
    return base.strip(), cats


def encode_nutrition_description(ingredients_text: str, categories: list[str]) -> str:
    base = ingredients_text.strip()
    valid = [c for c in categories if c in NUTRITION_CATEGORIES]
    if not valid:
        return base
    return f"{base}{NUTR_MARKER}{','.join(valid)}"


def _ingredient_library_hint() -> str:
    df = load_ingredients()
    if df.empty:
        return ""
    lines = []
    for _, row in df.iterrows():
        lines.append(f"{row['id']}: {row['name']} → {row['nutrition_category']}")
    return "\n".join(lines[:40])


def _local_analyze(ingredients_text: str) -> dict[str, Any]:
    matched_ids, unmatched = match_ingredients_from_text(ingredients_text)
    from src.nutrition import nutrition_coverage_for_menu

    draft = {"ingredient_ids": "|".join(matched_ids), "description": ingredients_text}
    cov = nutrition_coverage_for_menu(draft)
    categories = [cat for cat, v in cov.items() if v > 0]
    return {
        "categories": categories,
        "ingredient_ids": matched_ids,
        "unmatched": unmatched,
        "energy_tags": "手工添加",
        "source": "local",
        "note": "未配置 DeepSeek API，已使用本地食材库匹配（可能不完整）。",
    }


def analyze_ingredients(ingredients_text: str) -> dict[str, Any]:
    """
    Analyze ingredient text into seven nutrition categories.
    Uses DeepSeek-v4-flash when DEEPSEEK_API_KEY is set; otherwise local match.
    """
    text = ingredients_text.strip()
    if not text:
        return {
            "categories": [],
            "ingredient_ids": [],
            "unmatched": [],
            "energy_tags": "手工添加",
            "source": "none",
            "note": "请先填写食材。",
        }

    if not has_api_key():
        return _local_analyze(text)

    library = _ingredient_library_hint()
    cats = "、".join(NUTRITION_CATEGORIES)
    prompt = f"""根据用户输入的食材，判断覆盖了哪些营养类别，并尽量映射到食材库 ID。

用户食材：{text}

七大营养类别（只能从下列选）：{cats}

食材库（id: 名称 → 营养类）：
{library}

请返回 JSON：
{{
  "categories": ["蛋白质", ...],
  "ingredient_ids": ["ING_001", ...],
  "unmatched": ["用户写了但库中没有的食材"],
  "energy_tags": "快速供能·稳糖",
  "note": "一句中文说明"
}}

规则：
1. categories 必须是上述七类中的子集。
2. ingredient_ids 尽量从食材库 id 中选，匹配不到的放入 unmatched。
3. energy_tags 用 · 连接 1-3 个简短标签。"""

    try:
        raw = call_json(
            prompt,
            system_prompt="你是简愈一人食的营养分析助手。只输出 JSON，不要其他文字。",
            api_key_override=api_key(),
        )
        categories = [c for c in raw.get("categories", []) if c in NUTRITION_CATEGORIES]
        ids = [str(i) for i in raw.get("ingredient_ids", []) if str(i).startswith("ING_")]
        known = set(load_ingredients()["id"].tolist()) if not load_ingredients().empty else set()
        ids = [i for i in ids if i in known]
        if not ids:
            ids, _ = match_ingredients_from_text(text)
        if not categories and ids:
            from src.nutrition import nutrition_coverage_for_menu

            cov = nutrition_coverage_for_menu({"ingredient_ids": "|".join(ids), "description": text})
            categories = [c for c, v in cov.items() if v > 0]
        return {
            "categories": categories,
            "ingredient_ids": ids,
            "unmatched": [str(x) for x in raw.get("unmatched", [])],
            "energy_tags": str(raw.get("energy_tags", "手工添加")),
            "source": "api",
            "note": str(raw.get("note", "已由 DeepSeek 分析营养覆盖。")),
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
        result = _local_analyze(text)
        result["note"] = f"DeepSeek 调用失败，已改用本地匹配：{exc}"
        return result
