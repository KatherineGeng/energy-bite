"""Meal plan add/remove persistence tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import database as db
from src.meal_plan_utils import empty_meal_plan, flatten_plan


def _setup_tmp_data(tmp_path: Path, monkeypatch) -> str:
    monkeypatch.setattr(db, "DATA_PATH", tmp_path)
    monkeypatch.setattr(db, "APP_IMAGES_DIR", tmp_path / "app_images")
    user_key = "test_user_key_01"
    monkeypatch.setattr("src.client_profile.plan_user_key", lambda: user_key)
    monkeypatch.setattr("src.database.plan_user_key", lambda: user_key, raising=False)
    db.init_database(force=True)
    return user_key


def test_append_manual_and_persist_plan(tmp_path, monkeypatch):
    _setup_tmp_data(tmp_path, monkeypatch)
    menu_id = db.append_manual_menu(
        "萝卜鲫鱼汤",
        prep_minutes=20,
        ingredients_text="鲫鱼、萝卜",
        nutrition_categories=["蛋白质", "膳食纤维"],
        meal_type="午餐",
    )
    assert menu_id
    row = db.get_menu_by_id(menu_id)
    assert row is not None
    assert row["menu_name"] == "萝卜鲫鱼汤"

    plan = empty_meal_plan()
    plan["午餐"] = [menu_id, "MENU_001"]
    db.save_daily_meal_plan("2026-06-18", plan, confirmed=False)

    loaded = db.load_daily_meal_plan("2026-06-18")
    assert loaded is not None
    assert menu_id in loaded["plan"]["午餐"]
    assert "MENU_001" in loaded["plan"]["午餐"]


def test_remove_one_dish_keeps_others(tmp_path, monkeypatch):
    _setup_tmp_data(tmp_path, monkeypatch)
    manual_id = db.append_manual_menu("测试手工菜", meal_type="午餐")
    plan = empty_meal_plan()
    plan["午餐"] = ["MENU_001", manual_id]
    db.save_daily_meal_plan("2026-06-18", plan, confirmed=False)

    plan["午餐"] = [mid for mid in plan["午餐"] if mid != "MENU_001"]
    db.save_daily_meal_plan("2026-06-18", plan, confirmed=False)

    loaded = db.load_daily_meal_plan("2026-06-18")
    assert loaded is not None
    assert manual_id in loaded["plan"]["午餐"]
    assert "MENU_001" not in loaded["plan"]["午餐"]
    assert db.get_menu_by_id(manual_id) is not None


def test_plan_from_menu_ids_respects_slot(tmp_path, monkeypatch):
    _setup_tmp_data(tmp_path, monkeypatch)
    manual_id = db.append_manual_menu("午餐汤", meal_type="午餐")

    from src.meal_plan_utils import plan_from_menu_ids

    plan = plan_from_menu_ids(["MENU_001", manual_id], db.get_menu_by_id)
    assert manual_id in plan["午餐"]
