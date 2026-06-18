"""Geek share-code encode/decode for menu sharing."""

from __future__ import annotations

import re
from dataclasses import dataclass

PREFIX = "￥MENU:"
SUFFIX = "￥"


@dataclass
class ShareCodePayload:
    ingredient_ids: list[str]
    energy_tags: str
    estimated_score: float


class ShareCodeError(ValueError):
    pass


def _normalize_raw(code: str) -> str:
    text = code.strip()
    if PREFIX in text:
        text = text.split(PREFIX, 1)[1]
    elif text.upper().startswith("MENU:"):
        text = text[5:]
    if text.endswith(SUFFIX):
        text = text[: -len(SUFFIX)]
    return text.strip()


def encode_share_code(
    ingredient_ids: str | list[str],
    energy_tags: str,
    estimated_score: float = 0.0,
) -> str:
    if isinstance(ingredient_ids, list):
        ids_text = "|".join(ingredient_ids)
    else:
        ids_text = str(ingredient_ids).replace(",", "|")
    tags_text = str(energy_tags).strip()
    score = max(0.0, float(estimated_score))
    return f"{PREFIX}{ids_text}:{tags_text}:{score:.2f}{SUFFIX}"


def decode_share_code(code: str) -> ShareCodePayload:
    if not code or not str(code).strip():
        raise ShareCodeError("口令不能为空")

    if PREFIX not in code and not code.strip().upper().startswith("MENU:"):
        raise ShareCodeError("口令格式无效，需包含 ￥MENU: 前缀")

    body = _normalize_raw(code)
    parts = body.split(":")
    if len(parts) < 3:
        raise ShareCodeError("口令格式无效，应为 ￥MENU:食材ID:能量标签:预估分数￥")

    ingredient_part = parts[0].strip()
    score_part = parts[-1].strip()
    tags_part = ":".join(parts[1:-1]).strip()

    ingredient_ids = [x.strip() for x in re.split(r"[|,]", ingredient_part) if x.strip()]
    if not ingredient_ids:
        raise ShareCodeError("口令中未包含有效食材 ID")
    if not tags_part:
        raise ShareCodeError("口令中未包含能量标签")

    try:
        estimated_score = float(score_part)
    except ValueError as exc:
        raise ShareCodeError(f"预估分数无效: {score_part}") from exc

    for ing_id in ingredient_ids:
        if not re.match(r"^ING_\d{3}$", ing_id):
            raise ShareCodeError(f"食材 ID 格式无效: {ing_id}")

    return ShareCodePayload(
        ingredient_ids=ingredient_ids,
        energy_tags=tags_part,
        estimated_score=estimated_score,
    )
