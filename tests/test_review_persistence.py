"""Review draft helpers."""

from __future__ import annotations

from src.review_persistence import (
    collect_review_draft_from_session,
    day_section_complete,
    dish_section_complete,
    morning_section_complete,
    try_persist_day_section,
    try_persist_dish_section,
    try_save_morning_section,
)


class _FakeState(dict):
    def __getattr__(self, key: str):
        return self.get(key)

    def __setattr__(self, key: str, value) -> None:
        self[key] = value


def test_collect_review_draft_from_session(monkeypatch):
    fake = _FakeState(
        review_MENU_001_operation=4,
        review_MENU_001_nps=5,
        review_MENU_001_fav_dish=True,
        review_day_mood=3,
        review_day_energy=4,
        review_fav_full_day=False,
    )
    monkeypatch.setattr("src.review_persistence.st.session_state", fake)
    payload = collect_review_draft_from_session(["MENU_001"])
    assert payload["day_mood"] == 3
    assert payload["dishes"]["MENU_001"]["operation"] == 4
    assert payload["dishes"]["MENU_001"]["favorited"] is True


def test_merge_review_drafts_keeps_prior_scores():
    existing = {
        "day_mood": None,
        "day_energy": None,
        "fav_full_day": False,
        "dishes": {"MENU_001": {"operation": 4}},
        "completed": False,
    }
    fresh = {
        "day_mood": None,
        "day_energy": None,
        "fav_full_day": False,
        "dishes": {"MENU_001": {"nps": 5}},
        "completed": False,
    }
    from src.review_persistence import _merge_review_drafts

    merged = _merge_review_drafts(existing, fresh, ["MENU_001"])
    assert merged["dishes"]["MENU_001"]["operation"] == 4
    assert merged["dishes"]["MENU_001"]["nps"] == 5


def test_morning_section_complete(monkeypatch):
    fake = _FakeState(morning_sleep="良好", morning_load="中等")
    monkeypatch.setattr("src.review_persistence.st.session_state", fake)
    assert morning_section_complete() is False
    fake["morning_meal_count"] = 2
    assert morning_section_complete() is True


def test_dish_section_complete(monkeypatch):
    fake = _FakeState(review_M1_operation=3)
    monkeypatch.setattr("src.review_persistence.st.session_state", fake)
    assert dish_section_complete(["M1"]) is False
    fake["review_M1_nps"] = 4
    assert dish_section_complete(["M1"]) is True


def test_try_save_morning_waits_for_three(monkeypatch):
    fake = _FakeState(morning_sleep="良好")
    saved: list[tuple] = []
    monkeypatch.setattr("src.review_persistence.st.session_state", fake)
    monkeypatch.setattr(
        "src.review_persistence.save_morning_context",
        lambda day, sleep, load, count: saved.append((day, sleep, load, count)),
    )
    assert try_save_morning_section("2026-06-24") is False
    assert saved == []
    fake["morning_load"] = "低"
    fake["morning_meal_count"] = 3
    assert try_save_morning_section("2026-06-24") is True
    assert saved == [("2026-06-24", "良好", "低", 3)]


def test_persist_review_progress_saves_partial(monkeypatch):
    fake = _FakeState(review_M1_operation=3)
    calls: list[str] = []
    monkeypatch.setattr("src.review_persistence.st.session_state", fake)
    monkeypatch.setattr("src.review_persistence.review_day_submitted", lambda _d: False)
    monkeypatch.setattr(
        "src.review_persistence.persist_review_draft",
        lambda day, ids: calls.append(day),
    )
    from src.review_persistence import persist_review_progress

    persist_review_progress("2026-06-24", ["M1"])
    assert calls == ["2026-06-24"]


def test_try_persist_dish_section_waits(monkeypatch):
    fake = _FakeState(review_M1_operation=4)
    calls: list[str] = []
    monkeypatch.setattr("src.review_persistence.st.session_state", fake)
    monkeypatch.setattr("src.review_persistence.review_day_submitted", lambda _d: False)
    monkeypatch.setattr(
        "src.review_persistence.persist_review_draft",
        lambda day, ids: calls.append(day),
    )
    assert try_persist_dish_section("2026-06-24", ["M1"]) is False
    fake["review_M1_nps"] = 5
    assert try_persist_dish_section("2026-06-24", ["M1"]) is True
    assert calls == ["2026-06-24"]
