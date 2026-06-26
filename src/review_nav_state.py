"""Carry review/morning picks in URL so HTML chip clicks survive session loss."""

from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import quote

import streamlit as st

from src.nav_params import append_nav_params
from src.query_nav import pop_query_param, qp_first

_PICK_KEYS = (
    "morning_sleep",
    "morning_load",
    "morning_meal_count",
    "review_day_mood",
    "review_day_energy",
    "review_fav_full_day",
)


def _coerce_pick(key: str, value: Any) -> Any:
    if key in ("morning_meal_count", "review_day_mood", "review_day_energy"):
        return int(value)
    if key.endswith("_operation") or key.endswith("_nps"):
        return int(value)
    if key == "review_fav_full_day":
        return bool(value)
    if key.endswith("_fav_dish"):
        return bool(value)
    return value


def collect_pick_state() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in _PICK_KEYS:
        val = st.session_state.get(key)
        if val is not None:
            out[key] = val
    for key, val in st.session_state.items():
        if not isinstance(key, str):
            continue
        if key.startswith("review_") and key.endswith(("_operation", "_nps", "_fav_dish")):
            if val is not None:
                out[key] = val
    return out


def encode_pick_state(state: dict[str, Any]) -> str:
    raw = json.dumps(state, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_pick_state(token: str) -> dict[str, Any]:
    if not token:
        return {}
    pad = "=" * (-len(token) % 4)
    raw = base64.urlsafe_b64decode(token + pad)
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        return {}
    return {str(k): _coerce_pick(str(k), v) for k, v in data.items()}


def restore_review_picks_from_query() -> None:
    """Apply carried picks from ?rp= before hydrate runs."""
    token = pop_query_param("rp")
    if not token:
        return
    for key, value in decode_pick_state(token).items():
        st.session_state[key] = value


def is_review_chip_navigation() -> bool:
    return any(
        qp_first(key)
        for key in ("morning_pick", "review_score", "review_fav", "rp")
    )


def chip_nav_href(path_query: str) -> str:
    """HTML chip link — profile/auth suffix + in-progress pick state."""
    href = append_nav_params(path_query)
    state = collect_pick_state()
    if not state:
        return href
    token = encode_pick_state(state)
    return f"{href}&rp={quote(token)}"
