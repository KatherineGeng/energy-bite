"""Poster export facade — delegates to visualization V2 engine."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import streamlit as st

from src.visualization import generate_daily_poster, meals_for_poster_from_ids

__all__ = ["generate_daily_poster", "meals_for_poster_from_ids", "generate_poster"]


def _photo_fingerprint(photos: list[Any] | None) -> str:
    digest = hashlib.sha256()
    for item in photos or []:
        if isinstance(item, (bytes, bytearray)):
            digest.update(item)
        elif isinstance(item, str):
            digest.update(item.encode("utf-8"))
        else:
            digest.update(repr(item).encode("utf-8"))
    return digest.hexdigest()[:24]


def _photos_tuple(photos: list[Any] | None) -> tuple[bytes, ...]:
    out: list[bytes] = []
    for item in photos or []:
        if isinstance(item, (bytes, bytearray)):
            out.append(bytes(item))
    return tuple(out)


@st.cache_data(show_spinner=False, max_entries=12)
def _cached_generate_poster(
    date_str: str,
    meals_json: str,
    photos_fp: str,
    photos_blob: tuple[bytes, ...],
    theme: str,
) -> bytes:
    meals = json.loads(meals_json)
    photos = list(photos_blob) if photos_blob else None
    return generate_daily_poster(date_str=date_str, meals=meals, photos=photos, theme=theme)


def generate_poster(
    date_str: str,
    meals: list[dict] | None = None,
    menu_ids: list[str] | None = None,
    photos: list[Any] | None = None,
    theme: str = "",
    snapshots: dict[str, dict[str, str]] | None = None,
    plan: dict[str, list[str]] | None = None,
) -> bytes:
    if meals is None:
        meals = meals_for_poster_from_ids(menu_ids or [], snapshots=snapshots, plan=plan)
    meals_json = json.dumps(meals, ensure_ascii=False, sort_keys=True)
    photos_fp = _photo_fingerprint(photos)
    photos_blob = _photos_tuple(photos)
    return _cached_generate_poster(date_str, meals_json, photos_fp, photos_blob, theme)
