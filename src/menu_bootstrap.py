"""Browser localStorage backup for user menu library."""

from __future__ import annotations

import base64
import json
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from src.client_profile import plan_user_key
from src.query_nav import clear_query_key, qp_first


def _ls_key(user_key: str) -> str:
    return f"eb_user_menus_{user_key}"


def encode_menus_blob(records: list[dict[str, Any]]) -> str:
    raw = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_menus_blob(token: str) -> list[dict[str, Any]]:
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except Exception:
        pass
    return []


def sync_user_menus_to_browser() -> None:
    from src.menu_persistence import export_user_menus_for_browser

    user_key = plan_user_key()
    if not user_key:
        return
    records = export_user_menus_for_browser()
    if not records:
        return
    token = encode_menus_blob(records)
    safe = token.replace("\\", "\\\\").replace('"', '\\"')
    ls_key = _ls_key(user_key).replace('"', '\\"')
    components.html(
        f"""
        <script>
        try {{
          localStorage.setItem("{ls_key}", "{safe}");
        }} catch (e) {{}}
        </script>
        """,
        height=0,
        scrolling=False,
    )


def restore_menus_from_browser() -> None:
    if qp_first("ebmenus"):
        return
    if st.session_state.get("eb_menus_browser_checked"):
        return
    user_key = plan_user_key()
    if not user_key:
        st.session_state.eb_menus_browser_checked = True
        return
    ls_key = _ls_key(user_key).replace('"', '\\"')
    components.html(
        f"""
        <script>
        (function () {{
          try {{
            var stored = localStorage.getItem("{ls_key}");
            if (!stored) return;
            var u = new URL(window.parent.location.href);
            if (u.searchParams.get("ebmenus")) return;
            u.searchParams.set("ebmenus", stored);
            window.parent.location.replace(u.toString());
          }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        scrolling=False,
    )
    st.session_state.eb_menus_browser_checked = True


def menus_from_query_token() -> list[dict[str, Any]] | None:
    token = qp_first("ebmenus")
    if not token:
        return None
    clear_query_key("ebmenus")
    return decode_menus_blob(token)
