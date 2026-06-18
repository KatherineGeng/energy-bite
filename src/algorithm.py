"""NPS weight calculation for menu feedback."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.constants import MULTIPLIER_MAP, SCORE_MAX
from src.database import load_logs, load_menus, save_weights


def _round_half(value: float) -> float:
    return round(value * 2) / 2


def state_multiplier(mood_score: int, energy_score: int) -> float:
    avg = (mood_score + energy_score) / 2
    rounded = _round_half(avg)
    return MULTIPLIER_MAP.get(rounded, 1.0)


def base_score(nps_score: int, operation_score: int) -> float:
    """taste_score column stores NPS willingness (1-5)."""
    return (nps_score / SCORE_MAX) * 0.7 + (operation_score / SCORE_MAX) * 0.3


def final_weight_for_log(
    taste_score: int,
    operation_score: int,
    mood_score: int,
    energy_score: int,
) -> tuple[float, float, float]:
    base = base_score(taste_score, operation_score)
    multiplier = state_multiplier(mood_score, energy_score)
    return base, multiplier, base * multiplier


def aggregate_menu_weights(logs: pd.DataFrame) -> pd.DataFrame:
    menus = load_menus()
    if menus.empty:
        return pd.DataFrame(
            columns=[
                "menu_id",
                "base_score",
                "multiplier",
                "final_weight",
                "is_favorited",
                "log_count",
                "updated_at",
            ]
        )

    records: list[dict] = []
    now = datetime.now().isoformat(timespec="seconds")

    for menu_id in menus["menu_id"]:
        menu_logs = logs[logs["menu_id"] == menu_id] if not logs.empty else pd.DataFrame()
        if menu_logs.empty:
            records.append(
                {
                    "menu_id": menu_id,
                    "base_score": 0.0,
                    "multiplier": 1.0,
                    "final_weight": 0.0,
                    "is_favorited": False,
                    "log_count": 0,
                    "updated_at": now,
                }
            )
            continue

        weights: list[float] = []
        bases: list[float] = []
        mults: list[float] = []
        for _, row in menu_logs.iterrows():
            b, m, fw = final_weight_for_log(
                int(row["taste_score"]),
                int(row["operation_score"]),
                int(row["mood_score"]),
                int(row["energy_score"]),
            )
            bases.append(b)
            mults.append(m)
            weights.append(fw)

        records.append(
            {
                "menu_id": menu_id,
                "base_score": round(sum(bases) / len(bases), 4),
                "multiplier": round(sum(mults) / len(mults), 4),
                "final_weight": round(sum(weights) / len(weights), 4),
                "is_favorited": bool(menu_logs["is_favorited"].any()),
                "log_count": len(menu_logs),
                "updated_at": now,
            }
        )

    return pd.DataFrame(records)


def recalculate_weights() -> pd.DataFrame:
    logs = load_logs()
    weights = aggregate_menu_weights(logs)
    save_weights(weights)
    return weights
