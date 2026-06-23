"""Review draft helpers."""

from __future__ import annotations

from src.review_persistence import collect_review_draft_from_session


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
