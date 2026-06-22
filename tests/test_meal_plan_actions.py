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


def test_manual_menu_keeps_user_ingredient_text(tmp_path, monkeypatch):
    _setup_tmp_data(tmp_path, monkeypatch)
    menu_id = db.append_manual_menu(
        "萝卜鲫鱼汤",
        ingredients_text="萝卜，鲫鱼",
        ingredient_ids=[],
        nutrition_categories=["蛋白质"],
        meal_type="午餐",
    )
    row = db.get_menu_by_id(menu_id)
    assert row is not None
    from src.nutrition_api import parse_nutrition_from_description

    ing_text, _ = parse_nutrition_from_description(row["description"])
    assert "萝卜" in ing_text
    assert "鲫鱼" in ing_text
    assert "芦笋" not in ing_text


def test_radish_does_not_match_carrot(tmp_path, monkeypatch):
    _setup_tmp_data(tmp_path, monkeypatch)
    ids, unmatched = db.match_ingredients_from_text("萝卜，鲫鱼")
    assert "ING_020" not in ids
    assert "萝卜" in unmatched or "鲫鱼" in unmatched


def test_daily_plan_stores_menu_snapshots(tmp_path, monkeypatch):
    _setup_tmp_data(tmp_path, monkeypatch)
    menu_id = db.append_manual_menu(
        "盐姜西兰花",
        ingredients_text="西兰花、姜",
        ingredient_ids=[],
        meal_type="午餐",
    )
    plan = empty_meal_plan()
    plan["午餐"] = [menu_id]
    db.save_daily_meal_plan("2026-06-22", plan, confirmed=True)

    loaded = db.load_daily_meal_plan("2026-06-22")
    assert loaded is not None
    assert menu_id in loaded["snapshots"]
    assert loaded["snapshots"][menu_id]["menu_name"] == "盐姜西兰花"

    row = db.get_menu_row(menu_id, loaded["snapshots"])
    assert row is not None
    assert row["menu_name"] == "盐姜西兰花"


def test_append_manual_dedupes_by_name(tmp_path, monkeypatch):
    _setup_tmp_data(tmp_path, monkeypatch)
    first_id = db.append_manual_menu("萝卜鲫鱼汤", meal_type="午餐")
    second_id = db.append_manual_menu("萝卜鲫鱼汤", meal_type="晚餐")
    assert first_id == second_id
    hits = db.search_menus_by_keyword("萝卜鲫鱼汤")
    assert len(hits) == 1
    assert hits.iloc[0]["menu_id"] == first_id


def test_plan_from_menu_ids_respects_slot(tmp_path, monkeypatch):
    _setup_tmp_data(tmp_path, monkeypatch)
    manual_id = db.append_manual_menu("午餐汤", meal_type="午餐")

    from src.meal_plan_utils import plan_from_menu_ids

    plan = plan_from_menu_ids(["MENU_001", manual_id], db.get_menu_by_id)
    assert manual_id in plan["午餐"]
