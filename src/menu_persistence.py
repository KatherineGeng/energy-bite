"""Permanent user menu archive — survives app redeploy / version updates."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from src.client_profile import plan_user_key
from src.constants import DAILY_PLAN_FILE
from src.database import (
    DAILY_PLAN_COLUMNS,
    MENU_COLUMNS,
    MENU_FILE,
    _parse_plan_snapshots,
    _read_csv,
    _write_csv,
)

USER_MENUS_FILE = "user_menus.csv"
USER_MENUS_COLUMNS = [*MENU_COLUMNS, "user_key", "source", "saved_at"]


def _menu_row_dict(row: dict[str, Any] | pd.Series) -> dict[str, str]:
    return {col: str(row.get(col, "")) for col in MENU_COLUMNS}


def _upsert_menu_db(row: dict[str, str]) -> None:
    df = _read_csv(MENU_FILE, MENU_COLUMNS)
    mid = row["menu_id"]
    if not df.empty and mid in df["menu_id"].astype(str).tolist():
        idx = df[df["menu_id"].astype(str) == mid].index[-1]
        for col in MENU_COLUMNS:
            if col == "menu_id":
                continue
            val = row.get(col, "")
            if val:
                df.at[idx, col] = val
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    if "prep_minutes" in df.columns:
        df["prep_minutes"] = pd.to_numeric(df["prep_minutes"], errors="coerce").fillna(0).astype(int)
    _write_csv(df[MENU_COLUMNS], MENU_FILE)


def _upsert_user_archive(row: dict[str, str], *, user_key: str, source: str) -> None:
    df = _read_csv(USER_MENUS_FILE, USER_MENUS_COLUMNS)
    now = datetime.now().isoformat(timespec="seconds")
    record = {**row, "user_key": user_key, "source": source, "saved_at": now}
    if not df.empty and ((df["menu_id"] == row["menu_id"]) & (df["user_key"] == user_key)).any():
        idx = df[(df["menu_id"] == row["menu_id"]) & (df["user_key"] == user_key)].index[-1]
        for col in USER_MENUS_COLUMNS:
            if col in record and record[col]:
                df.at[idx, col] = record[col]
    else:
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    _write_csv(df[USER_MENUS_COLUMNS], USER_MENUS_FILE)


def persist_menu_record(
    row: dict[str, Any] | pd.Series,
    *,
    source: str = "manual",
    sync_browser: bool = True,
) -> None:
    """Write dish to user archive + menu_db (+ optional browser backup)."""
    from src.db_config import postgres_enabled

    user_key = plan_user_key()
    if not user_key:
        return
    clean = _menu_row_dict(row)
    if not clean.get("menu_id") or not clean.get("menu_name"):
        return
    if postgres_enabled():
        from src.pg_store import pg_upsert_user_menu

        pg_upsert_user_menu(clean, source=source)
        return
    _upsert_user_archive(clean, user_key=user_key, source=source)
    _upsert_menu_db(clean)
    if sync_browser:
        from src.user_vault import notify_user_data_changed

        notify_user_data_changed()


def find_menu_by_name(name: str) -> dict[str, str] | None:
    """Return existing dish by exact menu_name (menu_db + user archive)."""
    from src.db_config import postgres_enabled

    if postgres_enabled():
        from src.pg_store import pg_find_menu_by_name

        return pg_find_menu_by_name(name)
    q = name.strip()
    if not q:
        return None
    from src.database import load_menus

    seen_ids: set[str] = set()
    for df in (load_menus(), load_user_menu_archive()):
        if df.empty:
            continue
        exact = df[df["menu_name"].astype(str).str.strip() == q]
        for _, row in exact.iterrows():
            mid = str(row.get("menu_id", ""))
            if mid and mid not in seen_ids:
                seen_ids.add(mid)
                return _menu_row_dict(row)
    return None


def load_user_menu_archive(user_key: str | None = None) -> pd.DataFrame:
    from src.db_config import postgres_enabled

    if postgres_enabled():
        from src.pg_store import pg_load_user_menus

        return pg_load_user_menus(user_key)
    uk = user_key or plan_user_key()
    df = _read_csv(USER_MENUS_FILE, USER_MENUS_COLUMNS)
    if df.empty or not uk:
        return df
    scoped = df[df["user_key"].astype(str) == uk]
    legacy = df[df["user_key"].astype(str).str.strip().isin(["", "nan", "None"])]
    if scoped.empty and not legacy.empty:
        return legacy
    return scoped if not scoped.empty else df.iloc[0:0]


def rehydrate_menus_from_plan_snapshots(user_key: str | None = None) -> int:
    """Recover dishes embedded in saved daily plans."""
    uk = user_key or plan_user_key()
    if not uk:
        return 0
    plans = _read_csv(DAILY_PLAN_FILE, DAILY_PLAN_COLUMNS)
    if plans.empty:
        return 0
    rows = plans[plans["user_key"].astype(str) == uk]
    if rows.empty:
        rows = plans[plans["user_key"].astype(str).str.strip().isin(["", "nan", "None"])]
    count = 0
    seen: set[str] = set()
    for _, plan_row in rows.iterrows():
        snaps = _parse_plan_snapshots(str(plan_row.get("snapshots", "")))
        for mid, snap in snaps.items():
            if mid in seen:
                continue
            seen.add(mid)
            row = {"menu_id": mid, **snap}
            if row.get("menu_name"):
                persist_menu_record(row, source="plan_snapshot", sync_browser=False)
                count += 1
    if count:
        from src.user_vault import notify_user_data_changed

        notify_user_data_changed()
    return count


def rehydrate_user_menus_into_db(user_key: str | None = None) -> int:
    """Merge archived user menus back into active menu_db."""
    uk = user_key or plan_user_key()
    if not uk:
        return 0
    count = 0
    archive = load_user_menu_archive(uk)
    if not archive.empty:
        for _, row in archive.iterrows():
            _upsert_menu_db(_menu_row_dict(row))
            count += 1
    count += rehydrate_menus_from_plan_snapshots(uk)
    return count


def apply_menus_blob(records: list[dict[str, Any]]) -> int:
    """Merge menu rows decoded from browser backup."""
    user_key = plan_user_key()
    if not user_key or not records:
        return 0
    applied = 0
    for item in records:
        if not isinstance(item, dict):
            continue
        row = {col: str(item.get(col, "")) for col in MENU_COLUMNS}
        if row.get("menu_id") and row.get("menu_name"):
            persist_menu_record(row, source=str(item.get("source", "browser")))
            applied += 1
    return applied


def ensure_user_menus_rehydrated() -> None:
    from src.db_config import postgres_enabled

    if postgres_enabled():
        st.session_state._user_menus_rehydrated = True
        return
    if st.session_state.get("_user_menus_rehydrated"):
        return
    from src.menu_bootstrap import menus_from_query_token

    blob = menus_from_query_token()
    if blob:
        apply_menus_blob(blob)
    rehydrate_user_menus_into_db()
    st.session_state._user_menus_rehydrated = True


def merged_menu_library() -> pd.DataFrame:
    """Active menu_db plus user archive rows (deduped by menu_id)."""
    from src.database import MENU_COLUMNS, load_menus

    menus = load_menus()
    archive = load_user_menu_archive()
    if archive.empty:
        return menus
    extra = archive[[c for c in MENU_COLUMNS if c in archive.columns]].copy()
    if menus.empty:
        return extra.drop_duplicates(subset=["menu_id"], keep="last")
    combined = pd.concat([menus, extra], ignore_index=True)
    return combined.drop_duplicates(subset=["menu_id"], keep="last")


def export_user_menus_for_browser() -> list[dict[str, str]]:
    uk = plan_user_key()
    if not uk:
        return []
    archive = load_user_menu_archive(uk)
    if archive.empty:
        return []
    out: list[dict[str, str]] = []
    for _, row in archive.iterrows():
        out.append({col: str(row.get(col, "")) for col in MENU_COLUMNS})
        out[-1]["source"] = str(row.get("source", ""))
    return out
