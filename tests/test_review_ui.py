"""Review page must emit HTML chip layout (5.0.19 style)."""

from __future__ import annotations

from src.review_ui import dish_favorite_html, render_option_picker_html, render_score_picker_html


class _FakeSession(dict):
    def get(self, key, default=None):
        return super().get(key, default)


def test_score_picker_html_row(monkeypatch):
    import streamlit as st

    fake = _FakeSession(current_page="night")
    monkeypatch.setattr(st, "session_state", fake)
    captured: list[str] = []

    def _markdown(html: str, **kwargs):
        captured.append(html)

    monkeypatch.setattr(st, "markdown", _markdown)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(
        "src.review_ui.chip_nav_href",
        lambda url: url,
    )

    render_score_picker_html(
        "操作从容度 (1-5分)",
        "1：极其匆忙 → 5：优雅享受",
        "review_M001_operation",
        "M001",
        "operation",
        "2026-06-18",
    )

    row_html = next((h for h in captured if "eb-score-row" in h), "")
    assert "eb-score-chip" in row_html
    assert row_html.count("eb-score-chip") == 5
    assert "review_score=" in row_html
    label_html = next((h for h in captured if "eb-score-label" in h), "")
    assert "操作从容度" in label_html


def test_day_score_picker_html(monkeypatch):
    import streamlit as st

    fake = _FakeSession(current_page="night")
    monkeypatch.setattr(st, "session_state", fake)
    captured: list[str] = []

    def _markdown(html: str, **kwargs):
        captured.append(html)

    monkeypatch.setattr(st, "markdown", _markdown)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(
        "src.review_ui.chip_nav_href",
        lambda url: url,
    )

    render_score_picker_html(
        "情绪状态 (1-5分)",
        "1分：很低落 → 5分：很愉悦",
        "review_day_mood",
        "day",
        "mood",
        "2026-06-18",
    )

    row_html = next((h for h in captured if "eb-score-row" in h), "")
    assert "eb-score-chip" in row_html
    assert "day%3Amood%3A" in row_html or "day:mood" in row_html


def test_morning_option_picker_html(monkeypatch):
    import streamlit as st

    fake = _FakeSession(current_page="night", morning_sleep="良好")
    monkeypatch.setattr(st, "session_state", fake)
    captured: list[str] = []

    def _markdown(html: str, **kwargs):
        captured.append(html)

    monkeypatch.setattr(st, "markdown", _markdown)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(
        "src.review_ui.chip_nav_href",
        lambda url: url,
    )

    render_option_picker_html(
        "一、昨晚睡眠状态",
        "",
        "morning_sleep",
        ["很好", "良好", "一般", "较差"],
        "sleep",
    )

    row_html = next((h for h in captured if "eb-score-row" in h), "")
    assert row_html.count("eb-score-chip") == 4
    assert "selected" in row_html
    assert "morning_pick=" in row_html


def test_favorite_link_not_button(monkeypatch):
    import streamlit as st

    fake = _FakeSession(current_page="night")
    monkeypatch.setattr(st, "session_state", fake)
    monkeypatch.setattr(
        "src.review_ui.load_favorites_dishes",
        lambda: __import__("pandas").DataFrame(),
    )
    monkeypatch.setattr(
        "src.review_ui.chip_nav_href",
        lambda url: url,
    )

    html = dish_favorite_html("M001", "2026-06-18")
    assert 'class="eb-fav-link' in html
    assert "review_fav=" in html
    assert "stButton" not in html
