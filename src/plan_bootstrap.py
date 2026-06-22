"""Browser localStorage backup for daily meal plans (survives app reboot)."""

from __future__ import annotations

import base64
import json
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from src.client_profile import plan_user_key
from src.query_nav import qp_first


def _ls_key(user_key: str, day: str) -> str:
    return f"eb_daily_plan_{user_key}_{day}"


def encode_plan_blob(day: str, plan: dict[str, list[str]], *, confirmed: bool, snapshots: dict) -> str:
    payload = {
        "d": day,
        "p": {k: list(v) for k, v in plan.items()},
        "c": confirmed,
        "s": snapshots or {},
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_plan_blob(token: str) -> dict[str, Any] | None:
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        day = str(data.get("d", "")).strip()
        plan = data.get("p") or {}
        if not day or not isinstance(plan, dict):
            return None
        clean_plan = {
            "早餐": [str(x) for x in plan.get("早餐", []) if str(x).strip()],
            "午餐": [str(x) for x in plan.get("午餐", []) if str(x).strip()],
            "晚餐": [str(x) for x in plan.get("晚餐", []) if str(x).strip()],
        }
        menu_ids: list[str] = []
        for meal in ("早餐", "午餐", "晚餐"):
            menu_ids.extend(clean_plan.get(meal, []))
        if not menu_ids:
            return None
        return {
            "date": day,
            "plan": clean_plan,
            "menu_ids": menu_ids,
            "confirmed": bool(data.get("c")),
            "snapshots": data.get("s") or {},
        }
    except Exception:
        return None


def persist_plan_to_browser(day: str, plan: dict[str, list[str]], *, confirmed: bool, snapshots: dict) -> None:
    user_key = plan_user_key()
    if not user_key:
        return
    token = encode_plan_blob(day, plan, confirmed=confirmed, snapshots=snapshots)
    safe = token.replace("\\", "\\\\").replace('"', '\\"')
    ls_key = _ls_key(user_key, day).replace('"', '\\"')
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


def restore_plan_from_browser() -> None:
    """If URL has no ebplan but localStorage has today's plan, redirect once."""
    if qp_first("ebplan"):
        return
    if st.session_state.get("eb_plan_browser_checked"):
        return
    user_key = plan_user_key()
    if not user_key:
        st.session_state.eb_plan_browser_checked = True
        return
    day = st.session_state.get("today_date", "")
    ls_key = _ls_key(user_key, day).replace('"', '\\"')
    components.html(
        f"""
        <script>
        (function () {{
          try {{
            var stored = localStorage.getItem("{ls_key}");
            if (!stored) return;
            var u = new URL(window.parent.location.href);
            if (u.searchParams.get("ebplan")) return;
            u.searchParams.set("ebplan", stored);
            window.parent.location.replace(u.toString());
          }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        scrolling=False,
    )
    st.session_state.eb_plan_browser_checked = True


def plan_from_query_token() -> dict[str, Any] | None:
    token = qp_first("ebplan")
    if not token:
        return None
    return decode_plan_blob(token)
