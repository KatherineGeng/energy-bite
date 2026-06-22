"""Unified per-user data vault — survives Streamlit Cloud redeploy."""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.client_profile import plan_user_key
from src.constants import DAILY_PLAN_FILE
from src.database import (
    DAILY_PLAN_COLUMNS,
    FAVORITES_DISHES_COLUMNS,
    FAVORITES_DISHES_FILE,
    FAVORITES_MENUS_COLUMNS,
    FAVORITES_MENUS_FILE,
    LOG_COLUMNS,
    LOG_FILE,
    MORNING_CONTEXT_COLUMNS,
    MORNING_CONTEXT_FILE,
    _read_csv,
    _write_csv,
)

VAULT_SECTIONS = ("menus", "logs", "plans", "morning", "fav_dishes", "fav_menus", "posters")

_FRONTEND = str(Path(__file__).resolve().parent.parent / "components" / "vault_reader")
_vault_reader = components.declare_component("vault_reader", path=_FRONTEND)


def _ls_key(user_key: str, section: str) -> str:
    return f"eb_v_{user_key}_{section}"


def _compress_json(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(gzip.compress(raw)).decode("ascii")


def _decompress_json(token: str) -> Any:
    try:
        raw = gzip.decompress(base64.urlsafe_b64decode(token.encode("ascii")))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        try:
            return json.loads(base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8"))
        except Exception:
            return None


def read_vault_from_browser(user_key: str) -> dict[str, Any] | None:
    """Read all vault sections from localStorage via custom component."""
    if not user_key:
        return None
    raw = _vault_reader(user_key=user_key, key="eb_vault_reader", default=None)
    if raw is None:
        return None
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def persist_vault_to_browser(user_key: str, sections: dict[str, Any]) -> None:
    if not user_key or not sections:
        return
    lines: list[str] = []
    for section, payload in sections.items():
        if payload is None:
            continue
        token = _compress_json(payload).replace("\\", "\\\\").replace('"', '\\"')
        ls = _ls_key(user_key, section).replace('"', '\\"')
        lines.append(f'localStorage.setItem("{ls}", "{token}");')
    if not lines:
        return
    components.html(
        f"<script>try {{ {' '.join(lines)} }} catch (e) {{}}</script>",
        height=0,
        scrolling=False,
    )


def export_vault_sections(user_key: str | None = None) -> dict[str, Any]:
    uk = user_key or plan_user_key()
    if not uk:
        return {}

    from src.menu_persistence import export_user_menus_for_browser

    out: dict[str, Any] = {}
    menus = export_user_menus_for_browser()
    if menus:
        out["menus"] = menus

    log_cols = list(LOG_COLUMNS)
    if "user_key" not in log_cols:
        log_cols.append("user_key")
    logs = _read_csv(LOG_FILE, log_cols)
    if not logs.empty:
        scoped = logs[logs["user_key"].astype(str) == uk]
        legacy = logs[logs["user_key"].astype(str).str.strip().isin(["", "nan", "None"])]
        merged = pd.concat([scoped, legacy], ignore_index=True).drop_duplicates(subset=["log_id"], keep="last")
        if not merged.empty:
            out["logs"] = merged.to_dict("records")

    plans = _read_csv(DAILY_PLAN_FILE, DAILY_PLAN_COLUMNS)
    if not plans.empty:
        scoped = plans[plans["user_key"].astype(str) == uk]
        if scoped.empty:
            scoped = plans[plans["user_key"].astype(str).str.strip().isin(["", "nan", "None"])]
        if not scoped.empty:
            out["plans"] = scoped.to_dict("records")

    morning = _read_csv(MORNING_CONTEXT_FILE, MORNING_CONTEXT_COLUMNS)
    if not morning.empty:
        scoped = morning[morning["user_key"].astype(str) == uk]
        if scoped.empty:
            scoped = morning[morning["user_key"].astype(str).str.strip().isin(["", "nan", "None"])]
        if not scoped.empty:
            out["morning"] = scoped.to_dict("records")

    fav_d = _read_csv(FAVORITES_DISHES_FILE, FAVORITES_DISHES_COLUMNS)
    if not fav_d.empty:
        out["fav_dishes"] = fav_d.to_dict("records")

    fav_m = _read_csv(FAVORITES_MENUS_FILE, FAVORITES_MENUS_COLUMNS)
    if not fav_m.empty:
        out["fav_menus"] = fav_m.to_dict("records")

    posters = list(st.session_state.get("poster_history") or [])
    if posters:
        out["posters"] = posters

    return out


def sync_vault_to_browser() -> None:
    uk = plan_user_key()
    if not uk:
        return
    sections = export_vault_sections(uk)
    persist_vault_to_browser(uk, sections)


def notify_user_data_changed() -> None:
    """Push latest CSV state into browser localStorage (best-effort)."""
    try:
        sync_vault_to_browser()
    except Exception:
        pass


def _merge_rows(existing: pd.DataFrame, incoming: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    if existing.empty:
        return incoming
    if incoming.empty:
        return existing
    combined = pd.concat([existing, incoming], ignore_index=True)
    return combined.drop_duplicates(subset=key_cols, keep="last")


def _decode_section(raw: Any) -> list[dict[str, Any]] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, str):
        data = _decompress_json(raw)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        from src.menu_bootstrap import decode_menus_blob

        legacy = decode_menus_blob(raw)
        return legacy if legacy else None
    return None


def apply_vault_sections(data: dict[str, Any]) -> int:
    """Merge browser vault into server CSV files. Returns number of records applied."""
    uk = plan_user_key()
    if not uk or not data:
        return 0

    applied = 0

    menus_records = _decode_section(data.get("menus"))
    if menus_records:
        from src.menu_persistence import apply_menus_blob

        applied += apply_menus_blob(menus_records)

    section_specs = (
        ("logs", LOG_FILE, list(LOG_COLUMNS), ["log_id"]),
        ("plans", DAILY_PLAN_FILE, DAILY_PLAN_COLUMNS, ["date", "user_key"]),
        ("morning", MORNING_CONTEXT_FILE, MORNING_CONTEXT_COLUMNS, ["date", "user_key"]),
        ("fav_dishes", FAVORITES_DISHES_FILE, FAVORITES_DISHES_COLUMNS, ["fav_id"]),
        ("fav_menus", FAVORITES_MENUS_FILE, FAVORITES_MENUS_COLUMNS, ["fav_id"]),
    )
    for section, file_name, columns, key_cols in section_specs:
        records = _decode_section(data.get(section))
        if not records:
            continue
        incoming = pd.DataFrame(records)
        for col in columns:
            if col not in incoming.columns:
                incoming[col] = ""
        if section in ("plans", "morning", "logs") and "user_key" in columns:
            incoming["user_key"] = incoming["user_key"].replace("", uk).fillna(uk)
        existing = _read_csv(file_name, columns)
        merged = _merge_rows(existing, incoming[columns], key_cols)
        _write_csv(merged[columns], file_name)
        applied += len(incoming)

    posters_records = _decode_section(data.get("posters"))
    if posters_records:
        st.session_state.poster_history = posters_records
        applied += len(posters_records)

    return applied


def ensure_vault_synced() -> None:
    """Once per session: pull localStorage vault, merge into CSV, rehydrate menus."""
    uk = plan_user_key()
    if not uk:
        return
    flag = f"_vault_synced_{uk}"
    if st.session_state.get(flag):
        return

    payload = read_vault_from_browser(uk)
    if payload is not None:
        if payload:
            apply_vault_sections(payload)
            from src.menu_persistence import rehydrate_user_menus_into_db

            rehydrate_user_menus_into_db(uk)
            st.session_state.pop("_user_menus_rehydrated", None)
        st.session_state[flag] = True
        return

    if not st.session_state.get("_vault_reader_pass"):
        st.session_state._vault_reader_pass = True
        st.rerun()
