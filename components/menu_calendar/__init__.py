import os

import streamlit.components.v1 as components

_FRONTEND = os.path.join(os.path.dirname(__file__), "frontend")

_menu_calendar = components.declare_component("menu_calendar", path=_FRONTEND)


def render_menu_calendar(
    marked_dates: dict[str, str],
    selected_date: str,
    *,
    key: str | None = None,
) -> str | None:
    """
    Interactive month calendar. Dates with menus show a dot (green=confirmed, amber=draft).
    Returns selected ISO date string or None.
    """
    value = _menu_calendar(
        marked_dates=marked_dates,
        selected_date=selected_date,
        key=key,
        default=selected_date,
    )
    return str(value) if value else None
