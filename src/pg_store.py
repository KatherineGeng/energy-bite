"""PostgreSQL persistence — user menus, daily plans, morning context."""

from __future__ import annotations

import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from src.database import (
    INGREDIENTS_COLUMNS,
    MENU_COLUMNS,
    SEED_INGREDIENTS,
    SEED_MENUS,
    USER_PROFILE_COLUMNS,
)
from src.db_auth import current_user_id
from src.db_connection import pg_cursor
from src.meal_plan_utils import MEAL_ORDER

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "supabase" / "schema.sql"


def init_postgres_schema() -> None:
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    with pg_cursor(dict_rows=False) as cur:
        cur.execute(sql)


def seed_global_catalog() -> None:
    ing_df = pd.read_csv(StringIO(SEED_INGREDIENTS), dtype=str)
    menu_df = pd.read_csv(StringIO(SEED_MENUS), dtype=str)
    with pg_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM ingredients")
        if int(cur.fetchone()["n"]) == 0:
            for _, row in ing_df.iterrows():
                cur.execute(
                    """
                    INSERT INTO ingredients (id, name, nutrition_category, role, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    tuple(str(row[c]) for c in INGREDIENTS_COLUMNS),
                )
        cur.execute("SELECT COUNT(*) AS n FROM system_menus")
        if int(cur.fetchone()["n"]) == 0:
            for _, row in menu_df.iterrows():
                cur.execute(
                    """
                    INSERT INTO system_menus (
                        menu_id, menu_name, ingredient_ids, energy_tags,
                        meal_type, prep_minutes, description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (menu_id) DO NOTHING
                    """,
                    (
                        str(row["menu_id"]),
                        str(row["menu_name"]),
                        str(row["ingredient_ids"]),
                        str(row["energy_tags"]),
                        str(row["meal_type"]),
                        int(row.get("prep_minutes") or 15),
                        str(row.get("description") or ""),
                    ),
                )


def pg_load_ingredients() -> pd.DataFrame:
    with pg_cursor() as cur:
        cur.execute("SELECT id, name, nutrition_category, role, notes FROM ingredients ORDER BY id")
        rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=INGREDIENTS_COLUMNS)
    return pd.DataFrame([dict(r) for r in rows], columns=INGREDIENTS_COLUMNS)


def pg_load_system_menus() -> pd.DataFrame:
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT menu_id, menu_name, ingredient_ids, energy_tags,
                   meal_type, prep_minutes, description
            FROM system_menus ORDER BY menu_id
            """
        )
        rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=MENU_COLUMNS)
    df = pd.DataFrame([dict(r) for r in rows], columns=MENU_COLUMNS)
    df["prep_minutes"] = pd.to_numeric(df["prep_minutes"], errors="coerce").fillna(0).astype(int)
    return df


def pg_load_user_menus(user_id: str | None = None) -> pd.DataFrame:
    uid = user_id or current_user_id()
    if not uid:
        return pd.DataFrame(columns=[*MENU_COLUMNS, "user_key", "source", "saved_at"])
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT menu_id, menu_name, ingredient_ids, energy_tags, meal_type,
                   prep_minutes, description, source, saved_at
            FROM user_menus WHERE user_id = %s::uuid ORDER BY saved_at
            """,
            (uid,),
        )
        rows = cur.fetchall()
    cols = [*MENU_COLUMNS, "user_key", "source", "saved_at"]
    if not rows:
        return pd.DataFrame(columns=cols)
    out = []
    for r in rows:
        item = {c: str(r.get(c, "")) for c in MENU_COLUMNS}
        item["user_key"] = uid
        item["source"] = str(r.get("source") or "")
        item["saved_at"] = str(r.get("saved_at") or "")
        out.append(item)
    return pd.DataFrame(out, columns=cols)


def pg_load_menus_merged() -> pd.DataFrame:
    system = pg_load_system_menus()
    user = pg_load_user_menus()
    if user.empty:
        return system
    extra = user[[c for c in MENU_COLUMNS if c in user.columns]].copy()
    if system.empty:
        return extra.drop_duplicates(subset=["menu_id"], keep="last")
    combined = pd.concat([system, extra], ignore_index=True)
    return combined.drop_duplicates(subset=["menu_id"], keep="last")


def pg_get_menu_by_id(menu_id: str, user_id: str | None = None) -> dict[str, Any] | None:
    uid = user_id or current_user_id()
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT menu_id, menu_name, ingredient_ids, energy_tags,
                   meal_type, prep_minutes, description
            FROM system_menus WHERE menu_id = %s
            """,
            (menu_id,),
        )
        row = cur.fetchone()
        if row:
            return dict(row)
        if uid:
            cur.execute(
                """
                SELECT menu_id, menu_name, ingredient_ids, energy_tags,
                       meal_type, prep_minutes, description
                FROM user_menus WHERE user_id = %s::uuid AND menu_id = %s
                """,
                (uid, menu_id),
            )
            row = cur.fetchone()
            if row:
                return dict(row)
    return None


def pg_upsert_user_menu(row: dict[str, Any], *, source: str = "manual", cur: Any | None = None) -> None:
    uid = current_user_id()
    if not uid or not row.get("menu_id") or not row.get("menu_name"):
        return
    sql = """
        INSERT INTO user_menus (
            user_id, menu_id, menu_name, ingredient_ids, energy_tags,
            meal_type, prep_minutes, description, source, saved_at
        ) VALUES (
            %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        ON CONFLICT (user_id, menu_id) DO UPDATE SET
            menu_name = EXCLUDED.menu_name,
            ingredient_ids = EXCLUDED.ingredient_ids,
            energy_tags = EXCLUDED.energy_tags,
            meal_type = EXCLUDED.meal_type,
            prep_minutes = EXCLUDED.prep_minutes,
            description = EXCLUDED.description,
            source = EXCLUDED.source,
            saved_at = NOW()
    """
    params = (
        uid,
        str(row["menu_id"]),
        str(row["menu_name"]),
        str(row.get("ingredient_ids") or ""),
        str(row.get("energy_tags") or ""),
        str(row.get("meal_type") or "午餐"),
        int(row.get("prep_minutes") or 15),
        str(row.get("description") or ""),
        source,
    )
    if cur is not None:
        cur.execute(sql, params)
        return
    with pg_cursor() as inner:
        inner.execute(sql, params)


def pg_find_menu_by_name(name: str) -> dict[str, str] | None:
    q = name.strip()
    if not q:
        return None
    merged = pg_load_menus_merged()
    if merged.empty:
        return None
    exact = merged[merged["menu_name"].astype(str).str.strip() == q]
    if exact.empty:
        return None
    row = exact.iloc[-1]
    return {col: str(row.get(col, "")) for col in MENU_COLUMNS}


def _parse_plan_column(value: str) -> list[str]:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return []
    return [part.strip() for part in text.split("|") if part.strip()]


def pg_save_daily_meal_plan(
    day: str,
    plan: dict[str, list[str]],
    *,
    confirmed: bool,
    snapshots: dict,
    menu_source: str = "draft_plan",
) -> None:
    uid = current_user_id()
    if not uid:
        return
    with pg_cursor() as cur:
        cur.execute(
            """
            INSERT INTO daily_meal_plans (
                user_id, plan_date, breakfast, lunch, dinner, confirmed, snapshots, updated_at
            ) VALUES (%s::uuid, %s::date, %s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (user_id, plan_date) DO UPDATE SET
                breakfast = EXCLUDED.breakfast,
                lunch = EXCLUDED.lunch,
                dinner = EXCLUDED.dinner,
                confirmed = EXCLUDED.confirmed,
                snapshots = EXCLUDED.snapshots,
                updated_at = NOW()
            """,
            (
                uid,
                day,
                "|".join(plan.get("早餐", [])),
                "|".join(plan.get("午餐", [])),
                "|".join(plan.get("晚餐", [])),
                confirmed,
                json.dumps(snapshots, ensure_ascii=False),
            ),
        )
        for mid, snap in snapshots.items():
            if not snap.get("menu_name"):
                continue
            pg_upsert_user_menu({"menu_id": mid, **snap}, source=menu_source, cur=cur)


def pg_load_daily_meal_plan(day: str) -> dict[str, Any] | None:
    uid = current_user_id()
    if not uid:
        return None
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT plan_date, breakfast, lunch, dinner, confirmed, snapshots, updated_at
            FROM daily_meal_plans
            WHERE user_id = %s::uuid AND plan_date = %s::date
            """,
            (uid, day),
        )
        row = cur.fetchone()
    if not row:
        return None
    plan = {
        "早餐": _parse_plan_column(row["breakfast"]),
        "午餐": _parse_plan_column(row["lunch"]),
        "晚餐": _parse_plan_column(row["dinner"]),
    }
    menu_ids: list[str] = []
    for meal in MEAL_ORDER:
        menu_ids.extend(plan.get(meal, []))
    snaps = row.get("snapshots") or {}
    if isinstance(snaps, str):
        try:
            snaps = json.loads(snaps)
        except json.JSONDecodeError:
            snaps = {}
    return {
        "date": day,
        "plan": plan,
        "menu_ids": menu_ids,
        "confirmed": bool(row["confirmed"]),
        "updated_at": str(row.get("updated_at") or ""),
        "snapshots": snaps if isinstance(snaps, dict) else {},
    }


def pg_save_morning_context(day: str, sleep: str, load: str, meal_count: int) -> None:
    uid = current_user_id()
    if not uid:
        return
    with pg_cursor() as cur:
        cur.execute(
            """
            INSERT INTO morning_context (user_id, context_date, sleep, load, meal_count, updated_at)
            VALUES (%s::uuid, %s::date, %s, %s, %s, NOW())
            ON CONFLICT (user_id, context_date) DO UPDATE SET
                sleep = EXCLUDED.sleep,
                load = EXCLUDED.load,
                meal_count = EXCLUDED.meal_count,
                updated_at = NOW()
            """,
            (uid, day, sleep, load, int(meal_count)),
        )


def pg_load_morning_context(day: str) -> dict[str, Any] | None:
    uid = current_user_id()
    if not uid:
        return None
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT sleep, load, meal_count, updated_at
            FROM morning_context
            WHERE user_id = %s::uuid AND context_date = %s::date
            """,
            (uid, day),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "sleep": str(row["sleep"]),
        "load": str(row["load"]),
        "meal_count": int(row["meal_count"] or 3),
        "updated_at": str(row.get("updated_at") or ""),
    }


def pg_save_review_draft(day: str, payload: dict[str, Any]) -> None:
    uid = current_user_id()
    if not uid:
        return
    dishes = payload.get("dishes") or {}
    day_mood = payload.get("day_mood")
    day_energy = payload.get("day_energy")
    with pg_cursor() as cur:
        cur.execute(
            """
            INSERT INTO evening_review_drafts (
                user_id, review_date, day_mood, day_energy, fav_full_day,
                dish_scores, completed, updated_at
            ) VALUES (%s::uuid, %s::date, %s, %s, %s, %s::jsonb, %s, NOW())
            ON CONFLICT (user_id, review_date) DO UPDATE SET
                day_mood = EXCLUDED.day_mood,
                day_energy = EXCLUDED.day_energy,
                fav_full_day = EXCLUDED.fav_full_day,
                dish_scores = EXCLUDED.dish_scores,
                completed = EXCLUDED.completed,
                updated_at = NOW()
            """,
            (
                uid,
                day,
                int(day_mood) if day_mood is not None else None,
                int(day_energy) if day_energy is not None else None,
                bool(payload.get("fav_full_day", False)),
                json.dumps(dishes, ensure_ascii=False),
                bool(payload.get("completed", False)),
            ),
        )


def pg_save_poster_snapshot(day: str, png_bytes: bytes, menu_ids: list[str]) -> None:
    uid = current_user_id()
    if not uid:
        return
    menu_csv = ",".join(menu_ids)
    try:
        with pg_cursor() as cur:
            cur.execute(
                """
                INSERT INTO poster_snapshots (user_id, poster_date, png_data, menu_ids, updated_at)
                VALUES (%s::uuid, %s::date, %s, %s, NOW())
                ON CONFLICT (user_id, poster_date) DO UPDATE SET
                    png_data = EXCLUDED.png_data,
                    menu_ids = EXCLUDED.menu_ids,
                    updated_at = NOW()
                """,
                (uid, day, png_bytes, menu_csv),
            )
    except Exception:
        # Table may not exist until migration is applied — session cache still works.
        return


def pg_load_poster_snapshot(day: str) -> tuple[bytes, list[str]] | None:
    uid = current_user_id()
    if not uid:
        return None
    try:
        with pg_cursor() as cur:
            cur.execute(
                """
                SELECT png_data, menu_ids
                FROM poster_snapshots
                WHERE user_id = %s::uuid AND poster_date = %s::date
                """,
                (uid, day),
            )
            row = cur.fetchone()
    except Exception:
        return None
    if not row or not row.get("png_data"):
        return None
    raw_ids = str(row.get("menu_ids") or "")
    menu_ids = [x.strip() for x in raw_ids.split(",") if x.strip()]
    return bytes(row["png_data"]), menu_ids


def pg_load_review_draft(day: str) -> dict[str, Any] | None:
    uid = current_user_id()
    if not uid:
        return None
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT day_mood, day_energy, fav_full_day, dish_scores, completed, updated_at
            FROM evening_review_drafts
            WHERE user_id = %s::uuid AND review_date = %s::date
            """,
            (uid, day),
        )
        row = cur.fetchone()
    if not row:
        return None
    dishes = row.get("dish_scores") or {}
    if isinstance(dishes, str):
        dishes = json.loads(dishes)
    return {
        "day_mood": row.get("day_mood"),
        "day_energy": row.get("day_energy"),
        "fav_full_day": bool(row.get("fav_full_day")),
        "dishes": dishes if isinstance(dishes, dict) else {},
        "completed": bool(row.get("completed")),
        "updated_at": str(row.get("updated_at") or ""),
    }


def pg_load_all_user_profiles() -> pd.DataFrame:
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT id::text AS user_id, nickname, gender, age_group,
                   created_at::text AS created_at, updated_at::text AS updated_at
            FROM users ORDER BY created_at
            """
        )
        rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=USER_PROFILE_COLUMNS)
    df = pd.DataFrame([dict(r) for r in rows])
    df["client_ip"] = ""
    return df[USER_PROFILE_COLUMNS]


def pg_meal_plan_markers() -> dict[str, str]:
    uid = current_user_id()
    if not uid:
        return {}
    markers: dict[str, str] = {}
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT plan_date::text AS plan_date, confirmed, breakfast, lunch, dinner
            FROM daily_meal_plans
            WHERE user_id = %s::uuid
            """,
            (uid,),
        )
        for row in cur.fetchall():
            day = str(row["plan_date"])
            ids = (
                _parse_plan_column(row.get("breakfast", ""))
                + _parse_plan_column(row.get("lunch", ""))
                + _parse_plan_column(row.get("dinner", ""))
            )
            if not ids:
                continue
            markers[day] = "confirmed" if row.get("confirmed") else "draft"
    return markers


def pg_load_favorites_dishes() -> pd.DataFrame:
    from src.database import FAVORITES_DISHES_COLUMNS

    uid = current_user_id()
    if not uid:
        return pd.DataFrame(columns=FAVORITES_DISHES_COLUMNS)
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT fav_id, menu_id, fav_date::text AS date, saved_at::text AS saved_at
            FROM favorite_dishes
            WHERE user_id = %s::uuid
            ORDER BY saved_at
            """,
            (uid,),
        )
        rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=FAVORITES_DISHES_COLUMNS)
    return pd.DataFrame([dict(r) for r in rows], columns=FAVORITES_DISHES_COLUMNS)


def pg_load_favorites_menus() -> pd.DataFrame:
    from src.database import FAVORITES_MENUS_COLUMNS

    uid = current_user_id()
    if not uid:
        return pd.DataFrame(columns=FAVORITES_MENUS_COLUMNS)
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT fav_id, fav_date::text AS date, menu_ids, saved_at::text AS saved_at
            FROM favorite_menus
            WHERE user_id = %s::uuid
            ORDER BY saved_at
            """,
            (uid,),
        )
        rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=FAVORITES_MENUS_COLUMNS)
    return pd.DataFrame([dict(r) for r in rows], columns=FAVORITES_MENUS_COLUMNS)


def pg_save_favorite_dish(menu_id: str, date: str) -> None:
    uid = current_user_id()
    if not uid:
        return
    fav_id = f"FD_{date.replace('-', '')}_{menu_id}"
    with pg_cursor() as cur:
        cur.execute(
            """
            INSERT INTO favorite_dishes (fav_id, user_id, menu_id, fav_date, saved_at)
            VALUES (%s, %s::uuid, %s, %s::date, NOW())
            ON CONFLICT (fav_id) DO NOTHING
            """,
            (fav_id, uid, menu_id, date),
        )


def pg_remove_favorite_dish(menu_id: str, date: str) -> None:
    uid = current_user_id()
    if not uid:
        return
    with pg_cursor() as cur:
        cur.execute(
            """
            DELETE FROM favorite_dishes
            WHERE user_id = %s::uuid AND menu_id = %s AND fav_date = %s::date
            """,
            (uid, menu_id, date),
        )


def pg_save_favorite_menu_set(menu_ids: list[str], date: str) -> None:
    uid = current_user_id()
    if not uid:
        return
    ids_text = "|".join(menu_ids)
    fav_id = f"FM_{date.replace('-', '')}_{abs(hash(ids_text)) % 1000:03d}"
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM favorite_menus
            WHERE user_id = %s::uuid AND fav_date = %s::date AND menu_ids = %s
            """,
            (uid, date, ids_text),
        )
        if cur.fetchone():
            return
        cur.execute(
            """
            INSERT INTO favorite_menus (fav_id, user_id, fav_date, menu_ids, saved_at)
            VALUES (%s, %s::uuid, %s::date, %s, NOW())
            """,
            (fav_id, uid, date, ids_text),
        )


def pg_append_log(
    day: str,
    menu_id: str,
    *,
    nps_score: int,
    operation_score: int,
    mood_score: int,
    energy_score: int,
    is_favorited: bool,
    sleep_quality: str = "",
    brain_body_load: str = "",
    meal_count: int | None = None,
) -> str:
    uid = current_user_id()
    if not uid:
        return ""
    with pg_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM review_logs WHERE user_id = %s::uuid AND log_date = %s::date",
            (uid, day),
        )
        seq = int(cur.fetchone()["n"]) + 1
        log_id = f"LOG_{day.replace('-', '')}_{seq:03d}"
        cur.execute(
            """
            INSERT INTO review_logs (
                log_id, user_id, log_date, menu_id, taste_score, operation_score,
                mood_score, energy_score, is_favorited, sleep_quality, brain_body_load, meal_count
            ) VALUES (%s, %s::uuid, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                log_id,
                uid,
                day,
                menu_id,
                nps_score,
                operation_score,
                mood_score,
                energy_score,
                is_favorited,
                sleep_quality or "",
                brain_body_load or "",
                meal_count,
            ),
        )
    return log_id


def pg_load_logs() -> pd.DataFrame:
    from src.database import LOG_COLUMNS

    uid = current_user_id()
    if not uid:
        return pd.DataFrame(columns=LOG_COLUMNS)
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT log_id, log_date::text AS date, user_id::text AS user_key, menu_id,
                   taste_score, operation_score, mood_score, energy_score,
                   is_favorited, sleep_quality, brain_body_load, meal_count
            FROM review_logs
            WHERE user_id = %s::uuid
            ORDER BY log_date, log_id
            """,
            (uid,),
        )
        rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=LOG_COLUMNS)
    df = pd.DataFrame([dict(r) for r in rows], columns=LOG_COLUMNS)
    for col in ["taste_score", "operation_score", "mood_score", "energy_score", "meal_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["is_favorited"] = df["is_favorited"].astype(bool)
    return df


def pg_save_weights(df: pd.DataFrame) -> None:
    uid = current_user_id()
    if not uid or df.empty:
        return
    with pg_cursor() as cur:
        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT INTO menu_weights (
                    user_id, menu_id, base_score, multiplier, final_weight,
                    is_favorited, log_count, updated_at
                ) VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id, menu_id) DO UPDATE SET
                    base_score = EXCLUDED.base_score,
                    multiplier = EXCLUDED.multiplier,
                    final_weight = EXCLUDED.final_weight,
                    is_favorited = EXCLUDED.is_favorited,
                    log_count = EXCLUDED.log_count,
                    updated_at = NOW()
                """,
                (
                    uid,
                    str(row["menu_id"]),
                    float(row.get("base_score") or 0),
                    float(row.get("multiplier") or 1),
                    float(row.get("final_weight") or 0),
                    bool(row.get("is_favorited")),
                    int(row.get("log_count") or 0),
                ),
            )


def pg_load_weights() -> pd.DataFrame:
    from src.database import WEIGHTS_COLUMNS

    uid = current_user_id()
    if not uid:
        return pd.DataFrame(columns=WEIGHTS_COLUMNS)
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT menu_id, base_score, multiplier, final_weight,
                   is_favorited, log_count, updated_at::text AS updated_at
            FROM menu_weights
            WHERE user_id = %s::uuid
            ORDER BY menu_id
            """,
            (uid,),
        )
        rows = cur.fetchall()
    if not rows:
        return pd.DataFrame(columns=WEIGHTS_COLUMNS)
    df = pd.DataFrame([dict(r) for r in rows], columns=WEIGHTS_COLUMNS)
    for col in ["base_score", "multiplier", "final_weight"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["log_count"] = pd.to_numeric(df["log_count"], errors="coerce").fillna(0).astype(int)
    df["is_favorited"] = df["is_favorited"].astype(bool)
    return df
