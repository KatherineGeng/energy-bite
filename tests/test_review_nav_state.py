"""Review URL pick-state carry tests."""

from __future__ import annotations

from src.review_nav_state import decode_pick_state, encode_pick_state


def test_encode_decode_morning_picks():
    state = {"morning_sleep": "良好", "morning_load": "中等", "morning_meal_count": 2}
    token = encode_pick_state(state)
    restored = decode_pick_state(token)
    assert restored["morning_sleep"] == "良好"
    assert restored["morning_load"] == "中等"
    assert restored["morning_meal_count"] == 2


def test_encode_decode_review_scores():
    state = {
        "review_MENU_001_operation": 4,
        "review_MENU_001_nps": 5,
        "review_day_mood": 3,
    }
    token = encode_pick_state(state)
    restored = decode_pick_state(token)
    assert restored["review_MENU_001_operation"] == 4
    assert restored["review_MENU_001_nps"] == 5
    assert restored["review_day_mood"] == 3
