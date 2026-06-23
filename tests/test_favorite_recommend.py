"""Favorite menu recommendation tests."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import database as db
from src.favorite_recommend import recent_favorite_menu_candidates


def _setup(tmp_path: Path, monkeypatch) -> str:
    monkeypatch.setattr(db, "DATA_PATH", tmp_path)
    monkeypatch.setattr(db, "APP_IMAGES_DIR", tmp_path / "app_images")
    user_key = "test_user_key_01"
    monkeypatch.setattr("src.client_profile.plan_user_key", lambda: user_key)
    db.init_database(force=True)
    return user_key


def test_recent_favorite_menus_within_five_days(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    db.save_favorite_menu_set(["MENU_001", "MENU_002", "MENU_003"], "2026-06-20")
    db.save_favorite_menu_set(["MENU_004", "MENU_005", "MENU_006"], "2026-06-10")

    hits = recent_favorite_menu_candidates(within_days=5, as_of=date(2026, 6, 23))
    assert len(hits) == 1
    assert hits[0]["menu_ids"] == ["MENU_001", "MENU_002", "MENU_003"]


def test_recent_favorite_menus_exclude_confirmed_today(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    db.save_favorite_menu_set(["MENU_001", "MENU_002", "MENU_003"], "2026-06-22")
    db.save_favorite_menu_set(["MENU_004", "MENU_005", "MENU_006"], "2026-06-21")

    hits = recent_favorite_menu_candidates(
        within_days=5,
        exclude_menu_ids=["MENU_003", "MENU_001", "MENU_002"],
        as_of=date(2026, 6, 23),
    )
    assert len(hits) == 1
    assert hits[0]["menu_ids"] == ["MENU_004", "MENU_005", "MENU_006"]
