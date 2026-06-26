"""App calendar — always use Asia/Shanghai (北京时间)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

BEIJING_TZ = ZoneInfo("Asia/Shanghai")


def beijing_now() -> datetime:
    return datetime.now(BEIJING_TZ)


def beijing_today() -> date:
    return beijing_now().date()


def beijing_today_iso() -> str:
    return beijing_today().isoformat()
