"""CSV persistence layer for Energy Bite."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import re

import pandas as pd

from src.constants import (
    DAILY_PLAN_FILE,
    INGREDIENTS_FILE,
    LOG_FILE,
    MENU_FILE,
    MORNING_CONTEXT_FILE,
    SCORE_MAX,
    SCORE_MIN,
    WEIGHTS_FILE,
)
from src.meal_plan_utils import MEAL_ORDER, empty_meal_plan

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data"
ASSETS_GALLERY_DIR = PROJECT_ROOT / "assets" / "app_gallery"

FAVORITES_DISHES_FILE = "favorites_dishes.csv"
FAVORITES_MENUS_FILE = "favorites_menus.csv"

INGREDIENTS_COLUMNS = ["id", "name", "nutrition_category", "role", "notes"]
MENU_COLUMNS = [
    "menu_id",
    "menu_name",
    "ingredient_ids",
    "energy_tags",
    "meal_type",
    "prep_minutes",
    "description",
]
LOG_COLUMNS = [
    "log_id",
    "date",
    "menu_id",
    "taste_score",
    "operation_score",
    "mood_score",
    "energy_score",
    "is_favorited",
    "sleep_quality",
    "brain_body_load",
    "meal_count",
]
WEIGHTS_COLUMNS = [
    "menu_id",
    "base_score",
    "multiplier",
    "final_weight",
    "is_favorited",
    "log_count",
    "updated_at",
]
FAVORITES_DISHES_COLUMNS = ["fav_id", "menu_id", "date", "saved_at"]
FAVORITES_MENUS_COLUMNS = ["fav_id", "date", "menu_ids", "saved_at"]
MENU_ARCHIVE_FILE = "menu_archive.csv"
MENU_ARCHIVE_COLUMNS = [
    "archive_id",
    "date",
    "menu_ids",
    "is_shared",
    "is_favorited",
    "is_imported",
    "saved_at",
]
USER_PROFILE_FILE = "user_profiles.csv"
USER_PROFILE_COLUMNS = [
    "user_id",
    "client_ip",
    "nickname",
    "gender",
    "age_group",
    "created_at",
    "updated_at",
]
APP_IMAGES_FILE = "app_images.csv"
APP_IMAGES_COLUMNS = ["image_id", "filename", "source", "title", "created_at", "data_b64"]
APP_IMAGES_DIR = DATA_PATH / "app_images"
MORNING_CONTEXT_COLUMNS = ["date", "user_key", "sleep", "load", "meal_count", "updated_at"]
DAILY_PLAN_COLUMNS = [
    "date",
    "user_key",
    "breakfast",
    "lunch",
    "dinner",
    "confirmed",
    "updated_at",
    "snapshots",
]

SEED_INGREDIENTS = """id,name,nutrition_category,role,notes
ING_001,希腊酸奶(无糖),高钙|优质脂肪,主食|加餐,肠脑轴调节，提供色氨酸
ING_002,蓝莓/草莓,水果|膳食纤维,配菜|小食,强抗氧化，清除脑部自由基
ING_003,核桃,优质脂肪|Omega-3,小食|配菜,脑源性营养，抗神经炎症
ING_004,三文鱼,蛋白质|Omega-3,主食|主菜,构筑脑神经细胞膜核心物质
ING_005,藜麦糙米饭,谷物杂粮|膳食纤维,主食,低GI，平稳血糖防下午脑雾
ING_006,菠菜,膳食纤维|高钙,配菜,结合并排出肠道胆固醇
ING_007,嫩豆腐,蛋白质|植物雌激素,主菜|汤,补充类雌激素，缓解潮热焦虑
ING_008,番茄/菌菇,膳食纤维|维生素,配菜|汤,含萝卜硫素，辅助肝脏代谢脂肪
ING_009,初榨橄榄油,优质脂肪,调料,地中海核心，全天候心血管保护
ING_010,全麦吐司/全麦饼干,谷物杂粮|膳食纤维,主食,低GI稳定复合碳水
ING_011,牛油果,优质脂肪|膳食纤维,配菜|小食,富含单不饱和脂肪酸，抗脑雾
ING_012,水波蛋/鸡胸肉,蛋白质,主菜,优质氨基酸，维持肌肉与脑力
ING_013,无糖黑豆浆/豆浆,植物雌激素|高钙,加餐|主食,大豆异黄酮，温和调节雌激素
ING_014,全麦意面/皮塔饼,谷物杂粮|膳食纤维,主食,持续缓慢供能
ING_015,金枪鱼/沙丁鱼,蛋白质|Omega-3,主菜,深海优质多不饱和脂肪酸
ING_016,西兰花/羽衣甘蓝,膳食纤维|高钙,配菜,十字花科，富含萝卜硫素助肝脏代谢
ING_017,烤地中海杂蔬(彩椒/茄子/洋葱),膳食纤维|维生素,配菜,彩虹饮食，高抗氧化清除自由基
ING_018,鹰嘴豆/扁豆/白芸豆,蛋白质|膳食纤维,主食|主菜,高纤维慢碳水，强饱腹感稳血糖
ING_019,菲达奶酪/低脂奶酪,高钙|优质脂肪,配菜|小食,优质发酵乳制品，强健骨骼
ING_020,芦笋/胡萝卜/芹菜,膳食纤维|维生素,配菜,结合肠道胆固醇促进排出
ING_021,蒸红薯/水果玉米,谷物杂粮|膳食纤维,主食,天然原态膳食纤维
"""

SEED_MENUS = """menu_id,menu_name,ingredient_ids,energy_tags,meal_type,prep_minutes,description
MENU_001,醒脑酸奶浆果碗,ING_001|ING_002|ING_003,快速供能·肠脑舒缓,早餐,5,极简组装，零火候
MENU_002,抗炎三文鱼配低GI碳水,ING_004|ING_005|ING_006|ING_009,脑力续航·降胆固醇,午餐,15,单锅煎烤结合快炒
MENU_003,安神豆腐菌菇暖汤,ING_007|ING_008|ING_009,平稳褪黑素·雌激素补充,晚餐,20,切配后文火慢熬
MENU_004,牛油果水波蛋全麦吐司,ING_010|ING_011|ING_012|ING_013,稳糖能量·雌激素补充,早餐,10,全麦吐司抹牛油果泥，配水波蛋与黑豆浆
MENU_005,地中海金枪鱼番茄意面,ING_014|ING_008|ING_015|ING_016|ING_009,血管保护·高抗氧化,午餐,15,橄榄油炒香蒜末番茄，拌金枪鱼意面配西兰花
MENU_006,迷迭香烤沙丁鱼配烤杂蔬,ING_015|ING_017|ING_018|ING_009,神经抗炎·代谢平衡,晚餐,25,沙丁鱼与彩椒西葫芦改刀，橄榄油迷迭香慢烤
MENU_007,希腊能量酸奶燕麦饼干碗,ING_001|ING_003|ING_002|ING_010,强健骨骼·肠脑舒缓,早餐,5,希腊酸奶撒核桃蓝莓，搭配大麦若叶全麦饼干
MENU_008,柠檬蒜香鸡胸肉配希腊沙拉,ING_012|ING_019|ING_008|ING_009|ING_014,高钙高蛋白·脑力续航,午餐,20,烤鸡胸肉搭配黄瓜番茄菲达奶酪沙拉与皮塔饼
MENU_009,温润番茄慢炖扁豆汤,ING_018|ING_008|ING_020|ING_021|ING_009,平稳褪黑素·清肠排毒,晚餐,30,扁豆加番茄胡萝卜芹菜慢熬，配烤芦笋与蒸红薯
MENU_010,奇亚籽浆果隔夜燕麦杯,ING_021|ING_001|ING_002,快速供能·平稳控糖,早餐,5,前晚将燕麦奇亚籽泡入酸奶，清晨直接点缀树莓
MENU_011,姜黄香煎豆腐杂粮饭,ING_005|ING_007|ING_016|ING_009,代谢重启·植物雌激素,午餐,15,豆腐用姜黄黑胡椒少油煎制，配杂粮饭与炒羽衣甘蓝
MENU_012,西班牙冷汤配白豆三文鱼沙拉,ING_008|ING_018|ING_004|ING_009,高纤低脂·深海守护,晚餐,20,番茄青瓜打碎冷食，配白芸豆烟熏三文鱼沙拉
"""


def _csv_path(filename: str) -> Path:
    return DATA_PATH / filename


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _read_csv(filename: str, columns: list[str]) -> pd.DataFrame:
    path = _csv_path(filename)
    if not path.exists():
        return _empty_frame(columns)
    df = pd.read_csv(path, dtype=str)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def _write_csv(df: pd.DataFrame, filename: str) -> None:
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_csv(_csv_path(filename), index=False)


def init_database(force: bool = False) -> None:
    """Create data directory and seed CSV files if missing."""
    DATA_PATH.mkdir(parents=True, exist_ok=True)

    if force or not _csv_path(INGREDIENTS_FILE).exists():
        from io import StringIO

        df = pd.read_csv(StringIO(SEED_INGREDIENTS), dtype=str)
        _write_csv(df, INGREDIENTS_FILE)

    if force or not _csv_path(MENU_FILE).exists():
        from io import StringIO

        df = pd.read_csv(StringIO(SEED_MENUS), dtype=str)
        df["prep_minutes"] = pd.to_numeric(df["prep_minutes"], errors="coerce").fillna(0).astype(int)
        _write_csv(df, MENU_FILE)

    if force or not _csv_path(LOG_FILE).exists():
        _write_csv(_empty_frame(LOG_COLUMNS), LOG_FILE)

    if force or not _csv_path(WEIGHTS_FILE).exists():
        _write_csv(_empty_frame(WEIGHTS_COLUMNS), WEIGHTS_FILE)

    if force or not _csv_path(FAVORITES_DISHES_FILE).exists():
        _write_csv(_empty_frame(FAVORITES_DISHES_COLUMNS), FAVORITES_DISHES_FILE)

    if force or not _csv_path(FAVORITES_MENUS_FILE).exists():
        _write_csv(_empty_frame(FAVORITES_MENUS_COLUMNS), FAVORITES_MENUS_FILE)

    if force or not _csv_path(MORNING_CONTEXT_FILE).exists():
        _write_csv(_empty_frame(MORNING_CONTEXT_COLUMNS), MORNING_CONTEXT_FILE)

    if force or not _csv_path(DAILY_PLAN_FILE).exists():
        _write_csv(_empty_frame(DAILY_PLAN_COLUMNS), DAILY_PLAN_FILE)

    if force or not _csv_path(MENU_ARCHIVE_FILE).exists():
        _write_csv(_empty_frame(MENU_ARCHIVE_COLUMNS), MENU_ARCHIVE_FILE)

    if force or not _csv_path(USER_PROFILE_FILE).exists():
        _write_csv(_empty_frame(USER_PROFILE_COLUMNS), USER_PROFILE_FILE)

    APP_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    if force or not _csv_path(APP_IMAGES_FILE).exists():
        _write_csv(_empty_frame(APP_IMAGES_COLUMNS), APP_IMAGES_FILE)

    _migrate_legacy_favorites_to_archive()
    _migrate_legacy_daily_plans()


def _migrate_legacy_daily_plans() -> None:
    """Attach empty user_key rows to current user on next save; readable by legacy fallback."""
    df = _read_csv(DAILY_PLAN_FILE, DAILY_PLAN_COLUMNS)
    if df.empty or "user_key" not in df.columns:
        return
    # Ensure snapshots column exists for older files.
    if "snapshots" not in df.columns:
        df["snapshots"] = ""
        _write_csv(df, DAILY_PLAN_FILE)


def load_ingredients() -> pd.DataFrame:
    return _read_csv(INGREDIENTS_FILE, INGREDIENTS_COLUMNS)


def load_menus() -> pd.DataFrame:
    df = _read_csv(MENU_FILE, MENU_COLUMNS)
    if not df.empty and "prep_minutes" in df.columns:
        df["prep_minutes"] = pd.to_numeric(df["prep_minutes"], errors="coerce").fillna(0).astype(int)
    return df


def load_logs() -> pd.DataFrame:
    df = _read_csv(LOG_FILE, LOG_COLUMNS)
    if df.empty:
        return df
    for col in ["taste_score", "operation_score", "mood_score", "energy_score", "meal_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["is_favorited"] = df["is_favorited"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df


def load_weights() -> pd.DataFrame:
    df = _read_csv(WEIGHTS_FILE, WEIGHTS_COLUMNS)
    if df.empty:
        return df
    for col in ["base_score", "multiplier", "final_weight"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["log_count"] = pd.to_numeric(df["log_count"], errors="coerce").fillna(0).astype(int)
    df["is_favorited"] = df["is_favorited"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df


def save_weights(df: pd.DataFrame) -> None:
    out = df.copy()
    out["is_favorited"] = out["is_favorited"].map(lambda x: "true" if x else "false")
    _write_csv(out[WEIGHTS_COLUMNS], WEIGHTS_FILE)


def parse_list_field(value: str, seps: str = "|,") -> list[str]:
    """Split multi-value CSV field by pipe or comma."""
    if pd.isna(value) or not str(value).strip():
        return []
    text = str(value)
    for sep in seps[1:]:
        text = text.replace(sep, seps[0])
    return [part.strip() for part in text.split(seps[0]) if part.strip()]


def parse_energy_tags(value: str) -> list[str]:
    if pd.isna(value) or not str(value).strip():
        return []
    text = str(value).replace("·", "|").replace(",", "|")
    return [part.strip() for part in text.split("|") if part.strip()]


def append_log(
    date: str,
    menu_id: str,
    nps_score: int,
    operation_score: int,
    mood_score: int,
    energy_score: int,
    is_favorited: bool,
    sleep_quality: str = "",
    brain_body_load: str = "",
    meal_count: int | None = None,
) -> str:
    """Persist review log. nps_score is stored in taste_score column for weight algo."""
    for score, name in [
        (nps_score, "nps_score"),
        (operation_score, "operation_score"),
        (mood_score, "mood_score"),
        (energy_score, "energy_score"),
    ]:
        if not SCORE_MIN <= score <= SCORE_MAX:
            raise ValueError(f"{name} must be between {SCORE_MIN} and {SCORE_MAX}")

    df = load_logs()
    same_day = df[df["date"] == date]
    seq = len(same_day) + 1
    log_id = f"LOG_{date.replace('-', '')}_{seq:03d}"

    row = {
        "log_id": log_id,
        "date": date,
        "menu_id": menu_id,
        "taste_score": nps_score,
        "operation_score": operation_score,
        "mood_score": mood_score,
        "energy_score": energy_score,
        "is_favorited": "true" if is_favorited else "false",
        "sleep_quality": sleep_quality or "",
        "brain_body_load": brain_body_load or "",
        "meal_count": meal_count if meal_count is not None else "",
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(df, LOG_FILE)
    return log_id


def get_ingredient_map() -> dict[str, dict[str, str]]:
    df = load_ingredients()
    return {row["id"]: row.to_dict() for _, row in df.iterrows()}


def get_menu_by_id(menu_id: str) -> dict[str, Any] | None:
    df = load_menus()
    match = df[df["menu_id"] == menu_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def _snapshot_from_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "menu_name": str(row.get("menu_name", "")),
        "meal_type": str(row.get("meal_type", "")),
        "description": str(row.get("description", "")),
        "prep_minutes": str(row.get("prep_minutes", "15")),
        "ingredient_ids": str(row.get("ingredient_ids", "")),
        "energy_tags": str(row.get("energy_tags", "")),
    }


def _parse_plan_snapshots(raw: str) -> dict[str, dict[str, str]]:
    text = str(raw or "").strip()
    if not text or text.lower() == "nan":
        return {}
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return {str(k): dict(v) for k, v in data.items() if isinstance(v, dict)}
    except json.JSONDecodeError:
        pass
    return {}


def _build_plan_snapshots(
    plan: dict[str, list[str]],
    existing: dict[str, dict[str, str]] | None = None,
) -> dict[str, dict[str, str]]:
    from src.meal_plan_utils import flatten_plan

    snaps = dict(existing or {})
    for menu_id in flatten_plan(plan):
        if menu_id in snaps and snaps[menu_id].get("menu_name"):
            continue
        row = get_menu_by_id(menu_id)
        if row:
            snaps[menu_id] = _snapshot_from_row(row)
    return snaps


def get_menu_row(menu_id: str, snapshots: dict[str, dict[str, str]] | None = None) -> dict[str, Any] | None:
    """Menu from library, or from saved plan snapshot when library row is missing."""
    row = get_menu_by_id(menu_id)
    if row:
        return row
    snap = (snapshots or {}).get(menu_id)
    if not snap:
        return None
    return {
        "menu_id": menu_id,
        "menu_name": snap.get("menu_name", menu_id),
        "meal_type": snap.get("meal_type", "午餐"),
        "description": snap.get("description", ""),
        "prep_minutes": int(snap.get("prep_minutes") or 15),
        "ingredient_ids": snap.get("ingredient_ids", ""),
        "energy_tags": snap.get("energy_tags", ""),
    }


def get_logs_for_date(date: str) -> pd.DataFrame:
    df = load_logs()
    if df.empty:
        return df
    return df[df["date"] == date]


def get_log_history_for_share() -> pd.DataFrame:
    """All log records joined with menu info, newest first."""
    logs = load_logs()
    if logs.empty:
        return logs

    menus = load_menus()
    if menus.empty:
        logs = logs.copy()
        logs["menu_name"] = logs["menu_id"]
        logs["meal_type"] = ""
    else:
        logs = logs.merge(
            menus[["menu_id", "menu_name", "meal_type"]],
            on="menu_id",
            how="left",
        )

    logs["menu_name"] = logs["menu_name"].fillna(logs["menu_id"])
    logs["meal_type"] = logs["meal_type"].fillna("")
    logs = logs.sort_values(["date", "taste_score"], ascending=[False, False])

    def _label(row) -> str:
        star = " ⭐" if row.get("is_favorited") else ""
        meal = f"（{row['meal_type']}）" if row["meal_type"] else ""
        nps = int(row["taste_score"]) if pd.notna(row["taste_score"]) else 0
        return f"{row['date']} · {row['menu_name']}{meal} · NPS {nps}{star}"

    logs["label"] = logs.apply(_label, axis=1)
    return logs


def count_favorited_menus() -> int:
    dishes = load_favorites_dishes()
    menus = load_favorites_menus()
    dish_count = dishes["menu_id"].nunique() if not dishes.empty else 0
    menu_count = len(menus) if not menus.empty else 0
    return int(dish_count + menu_count)


def _flag_str(val: bool) -> str:
    return "1" if val else "0"


def _flag_bool(val: object) -> bool:
    return str(val).strip().lower() in ("1", "true", "yes")


def load_menu_archive() -> pd.DataFrame:
    return _read_csv(MENU_ARCHIVE_FILE, MENU_ARCHIVE_COLUMNS)


def record_menu_archive(
    day: str,
    menu_ids: list[str],
    *,
    is_shared: bool = False,
    is_favorited: bool = False,
    is_imported: bool = False,
) -> None:
    """Unified menu history — share / favorite / import flags on one row."""
    clean_ids = [mid.strip() for mid in menu_ids if mid and str(mid).strip()]
    if not clean_ids:
        return

    ids_text = "|".join(clean_ids)
    df = load_menu_archive()
    now = datetime.now().isoformat(timespec="seconds")

    if not df.empty:
        match = df[(df["date"] == day) & (df["menu_ids"] == ids_text)]
        if not match.empty:
            idx = match.index[-1]
            if is_shared:
                df.at[idx, "is_shared"] = "1"
            if is_favorited:
                df.at[idx, "is_favorited"] = "1"
            if is_imported:
                df.at[idx, "is_imported"] = "1"
            df.at[idx, "saved_at"] = now
            _write_csv(df, MENU_ARCHIVE_FILE)
            return

    archive_id = f"AR_{day.replace('-', '')}_{len(df) + 1:04d}"
    row = {
        "archive_id": archive_id,
        "date": day,
        "menu_ids": ids_text,
        "is_shared": _flag_str(is_shared),
        "is_favorited": _flag_str(is_favorited),
        "is_imported": _flag_str(is_imported),
        "saved_at": now,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(df, MENU_ARCHIVE_FILE)


def _migrate_legacy_favorites_to_archive() -> None:
    for _, row in _read_csv(FAVORITES_DISHES_FILE, FAVORITES_DISHES_COLUMNS).iterrows():
        if str(row.get("menu_id", "")).strip():
            record_menu_archive(
                str(row["date"]),
                [str(row["menu_id"])],
                is_favorited=True,
            )
    for _, row in _read_csv(FAVORITES_MENUS_FILE, FAVORITES_MENUS_COLUMNS).iterrows():
        ids = [x for x in str(row.get("menu_ids", "")).split("|") if x.strip()]
        if ids:
            record_menu_archive(str(row["date"]), ids, is_favorited=True)


def archive_date_markers() -> dict[str, str]:
    df = load_menu_archive()
    if df.empty:
        return {}
    markers: dict[str, str] = {}
    for _, row in df.iterrows():
        day = str(row.get("date", "")).strip()
        if not day or not str(row.get("menu_ids", "")).strip():
            continue
        if _flag_bool(row.get("is_shared")):
            markers[day] = "shared"
        elif _flag_bool(row.get("is_favorited")):
            markers[day] = "favorited"
        elif _flag_bool(row.get("is_imported")):
            markers[day] = "imported"
        elif day not in markers:
            markers[day] = "archive"
    return markers


def menu_ids_for_archive_date(day: str) -> list[str]:
    df = load_menu_archive()
    if df.empty:
        return []
    rows = df[df["date"] == day]
    out: list[str] = []
    seen: set[str] = set()
    for _, row in rows.iterrows():
        for mid in str(row.get("menu_ids", "")).split("|"):
            mid = mid.strip()
            if mid and mid not in seen:
                seen.add(mid)
                out.append(mid)
    return out


def all_menu_ids_for_date(day: str) -> list[str]:
    """Merge daily meal plan + unified archive for a date."""
    out: list[str] = []
    seen: set[str] = set()
    saved = load_daily_meal_plan(day)
    if saved:
        for mid in saved["menu_ids"]:
            if mid not in seen:
                seen.add(mid)
                out.append(mid)
    for mid in menu_ids_for_archive_date(day):
        if mid not in seen:
            seen.add(mid)
            out.append(mid)
    return out


def search_archive_menu_ids(keyword: str) -> list[str]:
    """Search menu names across archive entries."""
    text = keyword.strip()
    if len(text) < 1:
        return []
    df = load_menu_archive()
    if df.empty:
        return []
    hits: list[str] = []
    seen: set[str] = set()
    for _, row in df.iterrows():
        for mid in str(row.get("menu_ids", "")).split("|"):
            mid = mid.strip()
            if not mid or mid in seen:
                continue
            menu_row = get_menu_by_id(mid)
            if menu_row and text in str(menu_row.get("menu_name", "")):
                seen.add(mid)
                hits.append(mid)
    return hits


def dates_with_menus() -> set[str]:
    """All dates that have any saved menu for the current user."""
    from src.client_profile import plan_user_key
    from src.meal_plan_dates import meal_plan_date_markers

    return set(meal_plan_date_markers(plan_user_key()).keys())


def get_log_dates() -> set[str]:
    logs = load_logs()
    if logs.empty:
        return set()
    return set(str(d).strip() for d in logs["date"].unique() if str(d).strip())


def load_user_profile(client_ip: str = "") -> dict[str, Any] | None:
    df = _read_csv(USER_PROFILE_FILE, USER_PROFILE_COLUMNS)
    if df.empty:
        return None
    ip = str(client_ip or "").strip()
    if not ip:
        return None

    hits = df[df["client_ip"].astype(str).str.strip() == ip]
    if not hits.empty:
        row = hits.iloc[-1]
        return {col: str(row[col]) for col in USER_PROFILE_COLUMNS}

    blank = df[
        (df["client_ip"].astype(str).str.strip() == "")
        & (df["nickname"].astype(str).str.strip() != "")
    ]
    if len(blank) == 1:
        idx = blank.index[-1]
        df.at[idx, "client_ip"] = ip
        _write_csv(df, USER_PROFILE_FILE)
        row = df.loc[idx]
        return {col: str(row[col]) for col in USER_PROFILE_COLUMNS}

    return None


def save_user_profile(
    nickname: str,
    gender: str,
    age_group: str,
    client_ip: str = "",
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    df = _read_csv(USER_PROFILE_FILE, USER_PROFILE_COLUMNS)
    ip = str(client_ip or "").strip()
    nick = nickname.strip()

    if ip:
        mask = df["client_ip"].astype(str).str.strip() == ip
        if mask.any():
            idx = df[mask].index[-1]
            df.at[idx, "nickname"] = nick
            df.at[idx, "gender"] = gender
            df.at[idx, "age_group"] = age_group
            df.at[idx, "updated_at"] = now
            _write_csv(df, USER_PROFILE_FILE)
            return

    user_id = f"U{len(df) + 1:03d}"
    row = {
        "user_id": user_id,
        "client_ip": ip,
        "nickname": nick,
        "gender": gender,
        "age_group": age_group,
        "created_at": now,
        "updated_at": now,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(df, USER_PROFILE_FILE)


def load_all_user_profiles() -> pd.DataFrame:
    return _read_csv(USER_PROFILE_FILE, USER_PROFILE_COLUMNS)


def save_app_image(data: bytes, *, source: str = "user", title: str = "") -> str:
    APP_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    df = _read_csv(APP_IMAGES_FILE, APP_IMAGES_COLUMNS)
    image_id = f"IMG_{len(df) + 1:05d}"
    ext = ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        ext = ".png"
    filename = f"{image_id}{ext}"
    path = APP_IMAGES_DIR / filename
    path.write_bytes(data)
    row = {
        "image_id": image_id,
        "filename": filename,
        "source": source,
        "title": title or filename,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "data_b64": base64.b64encode(data).decode("ascii"),
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(df, APP_IMAGES_FILE)
    return image_id


def _static_gallery_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not ASSETS_GALLERY_DIR.is_dir():
        return rows
    for path in sorted(ASSETS_GALLERY_DIR.iterdir()):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        rows.append(
            {
                "image_id": f"STATIC_{path.stem}",
                "filename": path.name,
                "source": "static",
                "title": path.stem,
                "created_at": "",
                "data_b64": "",
            }
        )
    return rows


def list_app_images() -> list[dict[str, str]]:
    static_rows = _static_gallery_rows()
    df = _read_csv(APP_IMAGES_FILE, APP_IMAGES_COLUMNS)
    if df.empty:
        return static_rows
    df = df.sort_values("created_at", ascending=False)
    runtime = [dict(row) for _, row in df.iterrows()]
    static_ids = {r["image_id"] for r in static_rows}
    runtime = [r for r in runtime if str(r.get("image_id", "")) not in static_ids]
    return static_rows + runtime


def get_app_image_bytes(image_id: str) -> bytes | None:
    if str(image_id).startswith("STATIC_"):
        stem = str(image_id)[7:]
        if ASSETS_GALLERY_DIR.is_dir():
            for path in ASSETS_GALLERY_DIR.iterdir():
                if path.stem == stem and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    return path.read_bytes()
        return None

    df = _read_csv(APP_IMAGES_FILE, APP_IMAGES_COLUMNS)
    if df.empty:
        return None
    rows = df[df["image_id"] == image_id]
    if rows.empty:
        return None
    row = rows.iloc[-1]
    b64 = str(row.get("data_b64", "")).strip()
    if b64:
        try:
            return base64.b64decode(b64)
        except Exception:
            pass
    filename = str(row["filename"])
    path = APP_IMAGES_DIR / filename
    if path.exists():
        return path.read_bytes()
    return None


def delete_app_image(image_id: str) -> None:
    df = _read_csv(APP_IMAGES_FILE, APP_IMAGES_COLUMNS)
    if df.empty:
        return
    rows = df[df["image_id"] == image_id]
    if not rows.empty:
        filename = str(rows.iloc[-1]["filename"])
        path = APP_IMAGES_DIR / filename
        if path.exists():
            path.unlink()
    df = df[df["image_id"] != image_id]
    _write_csv(df, APP_IMAGES_FILE)


def load_favorites_dishes() -> pd.DataFrame:
    legacy = _read_csv(FAVORITES_DISHES_FILE, FAVORITES_DISHES_COLUMNS)
    archive = load_menu_archive()
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    if not archive.empty:
        fav_rows = archive[archive["is_favorited"] == "1"]
        for _, row in fav_rows.iterrows():
            mids = [x.strip() for x in str(row["menu_ids"]).split("|") if x.strip()]
            if len(mids) != 1:
                continue
            key = (str(row["date"]), mids[0])
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "fav_id": str(row["archive_id"]),
                    "menu_id": mids[0],
                    "date": str(row["date"]),
                    "saved_at": str(row["saved_at"]),
                }
            )

    if not legacy.empty:
        for _, row in legacy.iterrows():
            key = (str(row["date"]), str(row["menu_id"]))
            if key in seen:
                continue
            seen.add(key)
            rows.append({col: str(row[col]) for col in FAVORITES_DISHES_COLUMNS})

    if not rows:
        return _empty_frame(FAVORITES_DISHES_COLUMNS)
    return pd.DataFrame(rows, columns=FAVORITES_DISHES_COLUMNS)


def load_favorites_menus() -> pd.DataFrame:
    legacy = _read_csv(FAVORITES_MENUS_FILE, FAVORITES_MENUS_COLUMNS)
    archive = load_menu_archive()
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    if not archive.empty:
        fav_rows = archive[archive["is_favorited"] == "1"]
        for _, row in fav_rows.iterrows():
            ids_text = str(row["menu_ids"])
            mids = [x.strip() for x in ids_text.split("|") if x.strip()]
            if len(mids) < 2:
                continue
            key = (str(row["date"]), ids_text)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "fav_id": str(row["archive_id"]),
                    "date": str(row["date"]),
                    "menu_ids": ids_text,
                    "saved_at": str(row["saved_at"]),
                }
            )

    if not legacy.empty:
        for _, row in legacy.iterrows():
            key = (str(row["date"]), str(row["menu_ids"]))
            if key in seen:
                continue
            seen.add(key)
            rows.append({col: str(row[col]) for col in FAVORITES_MENUS_COLUMNS})

    if not rows:
        return _empty_frame(FAVORITES_MENUS_COLUMNS)
    return pd.DataFrame(rows, columns=FAVORITES_MENUS_COLUMNS)


def save_favorite_dish(menu_id: str, date: str) -> None:
    df = load_favorites_dishes()
    if not df.empty and ((df["menu_id"] == menu_id) & (df["date"] == date)).any():
        return
    fav_id = f"FD_{date.replace('-', '')}_{menu_id}"
    row = {
        "fav_id": fav_id,
        "menu_id": menu_id,
        "date": date,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    legacy = _read_csv(FAVORITES_DISHES_FILE, FAVORITES_DISHES_COLUMNS)
    legacy = pd.concat([legacy, pd.DataFrame([row])], ignore_index=True)
    _write_csv(legacy, FAVORITES_DISHES_FILE)
    record_menu_archive(date, [menu_id], is_favorited=True)


def remove_favorite_dish(menu_id: str, date: str) -> None:
    legacy = _read_csv(FAVORITES_DISHES_FILE, FAVORITES_DISHES_COLUMNS)
    if not legacy.empty:
        legacy = legacy[~((legacy["menu_id"] == menu_id) & (legacy["date"] == date))]
        _write_csv(legacy, FAVORITES_DISHES_FILE)
    archive = load_menu_archive()
    if not archive.empty:
        mask = (archive["date"] == date) & (archive["menu_ids"] == menu_id)
        if mask.any():
            idx = archive[mask].index[-1]
            archive.at[idx, "is_favorited"] = "0"
            _write_csv(archive, MENU_ARCHIVE_FILE)


def save_favorite_menu_set(menu_ids: list[str], date: str) -> None:
    df = load_favorites_menus()
    ids_text = "|".join(menu_ids)
    existing = df[(df["date"] == date) & (df["menu_ids"] == ids_text)] if not df.empty else pd.DataFrame()
    if not existing.empty:
        return
    fav_id = f"FM_{date.replace('-', '')}_{len(df) + 1:03d}"
    row = {
        "fav_id": fav_id,
        "date": date,
        "menu_ids": ids_text,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(df, FAVORITES_MENUS_FILE)
    record_menu_archive(date, menu_ids, is_favorited=True)


def next_menu_id() -> str:
    df = load_menus()
    if df.empty:
        return "MENU_001"
    nums: list[int] = []
    for menu_id in df["menu_id"]:
        if str(menu_id).startswith("MENU_"):
            try:
                nums.append(int(str(menu_id).split("_")[1]))
            except (IndexError, ValueError):
                continue
    return f"MENU_{max(nums, default=0) + 1:03d}"


def get_menu_weight(menu_id: str) -> float:
    weights = load_weights()
    if weights.empty:
        return 0.0
    match = weights[weights["menu_id"] == menu_id]
    if match.empty:
        return 0.0
    return float(match.iloc[0]["final_weight"])


def get_menu_pick_counts() -> dict[str, int]:
    """How often each menu was chosen (logs + weight log_count)."""
    counts: dict[str, int] = {}
    logs = load_logs()
    if not logs.empty:
        for menu_id, n in logs["menu_id"].value_counts().items():
            counts[str(menu_id)] = int(n)

    weights = load_weights()
    if not weights.empty:
        for _, row in weights.iterrows():
            menu_id = str(row["menu_id"])
            log_count = int(row.get("log_count") or 0)
            if log_count:
                counts[menu_id] = counts.get(menu_id, 0) + log_count
    return counts


def get_menus_by_pick_frequency() -> pd.DataFrame:
    """All menus sorted by selection frequency (desc), then name."""
    menus = load_menus()
    if menus.empty:
        return menus

    counts = get_menu_pick_counts()
    menus = menus.copy()
    menus["pick_count"] = menus["menu_id"].map(lambda mid: counts.get(str(mid), 0))
    menus = menus.sort_values(["pick_count", "menu_name"], ascending=[False, True])
    return menus


def search_menus_by_keyword(query: str, limit: int = 6) -> pd.DataFrame:
    """Fuzzy match menu names in the library (case-insensitive substring)."""
    q = query.strip()
    if len(q) < 2:
        return _empty_frame(MENU_COLUMNS)

    menus = load_menus()
    if menus.empty:
        return menus

    mask = menus["menu_name"].str.contains(q, case=False, na=False)
    # Also match description and energy tags
    for col in ("description", "energy_tags"):
        if col in menus.columns:
            mask = mask | menus[col].astype(str).str.contains(q, case=False, na=False)

    hits = menus[mask].copy()
    if hits.empty:
        return hits

    counts = get_menu_pick_counts()
    hits["pick_count"] = hits["menu_id"].map(lambda mid: counts.get(str(mid), 0))
    return hits.sort_values(["pick_count", "menu_name"], ascending=[False, True]).head(limit)


def _ingredient_token_match(token: str, library_name: str) -> bool:
    """Match user token to library name without false positives (e.g. 萝卜 ≠ 胡萝卜)."""
    token = token.strip().lower()
    name = str(library_name).strip()
    if not token or not name:
        return False
    if name.lower() == token:
        return True
    for segment in re.split(r"[/、|（(]", name):
        seg = segment.strip().lower()
        if seg == token:
            return True
        if seg.startswith(token) and "(" in name:
            return True
    return False


def match_ingredients_from_text(text: str) -> tuple[list[str], list[str]]:
    """
    Match free-text ingredient names to ingredient library IDs.
    Returns (matched_ids, unmatched_user_tokens).
    """
    raw = text.strip()
    if not raw:
        return [], []

    parts = [p.strip() for p in re.split(r"[、,，/|+\s]+", raw) if p.strip()]
    ings = load_ingredients()
    if ings.empty:
        return [], parts

    matched_ids: list[str] = []
    unmatched: list[str] = []

    for part in parts:
        hit = ings[ings["name"].str.lower() == part.lower()]
        if hit.empty:
            hit = ings[
                ings["name"].apply(lambda n: _ingredient_token_match(part, str(n)))
            ]
        if not hit.empty:
            ing_id = str(hit.iloc[0]["id"])
            if ing_id not in matched_ids:
                matched_ids.append(ing_id)
        else:
            unmatched.append(part)

    return matched_ids, unmatched


def append_manual_menu(
    menu_name: str,
    prep_minutes: int = 15,
    ingredients_text: str = "",
    ingredient_ids: list[str] | None = None,
    energy_tags: str = "手工添加",
    description: str = "",
    meal_type: str = "午餐",
    nutrition_categories: list[str] | None = None,
) -> str:
    """Create a hand-entered dish in the menu library."""
    from src.nutrition_api import encode_nutrition_description

    if ingredient_ids is not None:
        ids = list(ingredient_ids)
    elif ingredients_text.strip():
        ids, _ = match_ingredients_from_text(ingredients_text)
    else:
        ids = []

    if ids:
        known = set(load_ingredients()["id"].tolist())
        missing = [i for i in ids if i not in known]
        if missing:
            raise ValueError(f"未知食材 ID: {', '.join(missing)}")

    ing_text = ingredients_text.strip()
    if nutrition_categories:
        desc = encode_nutrition_description(ing_text, nutrition_categories)
    elif description.strip():
        desc = description.strip()
    else:
        desc = ing_text or "手工添加"

    df = load_menus()
    menu_id = next_menu_id()
    ids_text = "|".join(ids)
    tags = parse_energy_tags(energy_tags)
    tags_text = "·".join(tags) if tags else energy_tags

    row = {
        "menu_id": menu_id,
        "menu_name": menu_name.strip(),
        "ingredient_ids": ids_text,
        "energy_tags": tags_text,
        "meal_type": meal_type,
        "prep_minutes": int(prep_minutes),
        "description": desc,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(df, MENU_FILE)
    return menu_id


def append_menu_from_share(
    ingredient_ids: list[str],
    energy_tags: str,
    menu_name: str = "",
    meal_type: str = "午餐",
    prep_minutes: int = 15,
    description: str = "由极客口令导入",
) -> str:
    known = set(load_ingredients()["id"].tolist())
    missing = [ing_id for ing_id in ingredient_ids if ing_id not in known]
    if missing:
        raise ValueError(f"未知食材 ID: {', '.join(missing)}")

    df = load_menus()
    menu_id = next_menu_id()
    ids_text = "|".join(ingredient_ids)
    tags = parse_energy_tags(energy_tags)
    tags_text = "·".join(tags) if tags else energy_tags

    if not menu_name:
        menu_name = f"{tags[0]}组合" if tags else "好友分享菜单"

    row = {
        "menu_id": menu_id,
        "menu_name": menu_name,
        "ingredient_ids": ids_text,
        "energy_tags": tags_text,
        "meal_type": meal_type,
        "prep_minutes": int(prep_minutes),
        "description": description,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(df, MENU_FILE)
    today = datetime.now().date().isoformat()
    record_menu_archive(today, [menu_id], is_imported=True)
    return menu_id


def _parse_plan_column(value: str) -> list[str]:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return []
    return [part.strip() for part in text.split("|") if part.strip() and part.strip().lower() != "nan"]


def _plan_dict_from_row(row: pd.Series) -> dict[str, list[str]]:
    return {
        "早餐": _parse_plan_column(row.get("breakfast", "")),
        "午餐": _parse_plan_column(row.get("lunch", "")),
        "晚餐": _parse_plan_column(row.get("dinner", "")),
    }


def save_daily_meal_plan(day: str, plan: dict[str, list[str]], *, confirmed: bool) -> None:
    """Persist draft or confirmed meal plan for a date (scoped by user)."""
    from src.client_profile import plan_user_key

    user_key = plan_user_key()
    if not user_key:
        return

    df = _read_csv(DAILY_PLAN_FILE, DAILY_PLAN_COLUMNS)
    prev_snaps: dict[str, dict[str, str]] = {}
    if not df.empty:
        mask = (df["date"] == day) & (df["user_key"] == user_key)
        prev_rows = df[mask]
        if not prev_rows.empty:
            prev_snaps = _parse_plan_snapshots(str(prev_rows.iloc[-1].get("snapshots", "")))

    snapshots = _build_plan_snapshots(plan, prev_snaps)
    row = {
        "date": day,
        "user_key": user_key,
        "breakfast": "|".join(plan.get("早餐", [])),
        "lunch": "|".join(plan.get("午餐", [])),
        "dinner": "|".join(plan.get("晚餐", [])),
        "confirmed": "true" if confirmed else "false",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "snapshots": json.dumps(snapshots, ensure_ascii=False),
    }
    if df.empty:
        out = pd.DataFrame([row])
    else:
        mask = (df["date"] == day) & (df["user_key"] == user_key)
        df = df[~mask]
        out = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(out[DAILY_PLAN_COLUMNS], DAILY_PLAN_FILE)


def load_daily_meal_plan(day: str) -> dict[str, Any] | None:
    from src.client_profile import plan_user_key

    user_key = plan_user_key()
    if not user_key:
        return None

    df = _read_csv(DAILY_PLAN_FILE, DAILY_PLAN_COLUMNS)
    if df.empty:
        return None
    rows = df[(df["date"] == day) & (df["user_key"] == user_key)]
    if rows.empty:
        legacy = df[
            (df["date"] == day)
            & (df["user_key"].astype(str).str.strip().isin(["", "nan", "None"]))
        ]
        if not legacy.empty:
            rows = legacy
            idx = rows.index[-1]
            df.at[idx, "user_key"] = user_key
            _write_csv(df, DAILY_PLAN_FILE)
    if rows.empty:
        return None
    row = rows.iloc[-1]
    plan = _plan_dict_from_row(row)
    menu_ids: list[str] = []
    for meal in MEAL_ORDER:
        menu_ids.extend(plan.get(meal, []))
    confirmed = str(row.get("confirmed", "")).lower() in ("true", "1", "yes")
    snapshots = _parse_plan_snapshots(str(row.get("snapshots", "")))
    return {
        "date": day,
        "plan": plan,
        "menu_ids": menu_ids,
        "confirmed": confirmed,
        "updated_at": str(row.get("updated_at", "")),
        "snapshots": snapshots,
    }


def list_meal_plan_dates(*, confirmed_only: bool = False) -> list[str]:
    from src.client_profile import plan_user_key

    user_key = plan_user_key()
    df = _read_csv(DAILY_PLAN_FILE, DAILY_PLAN_COLUMNS)
    if df.empty:
        return []
    if user_key:
        scoped = df[
            (df["user_key"] == user_key)
            | (df["user_key"].astype(str).str.strip().isin(["", "nan", "None"]))
        ]
        df = scoped if not scoped.empty else df
    if confirmed_only:
        df = df[df["confirmed"].astype(str).str.lower().isin(["true", "1", "yes"])]
    dates = sorted(df["date"].astype(str).unique().tolist(), reverse=True)
    return dates


def load_morning_context(day: str) -> dict[str, Any] | None:
    from src.client_profile import plan_user_key

    user_key = plan_user_key()
    if not user_key:
        return None

    df = _read_csv(MORNING_CONTEXT_FILE, MORNING_CONTEXT_COLUMNS)
    if df.empty:
        return None
    rows = df[(df["date"] == day) & (df["user_key"] == user_key)]
    if rows.empty:
        return None
    row = rows.iloc[-1]
    return {
        "sleep": str(row["sleep"]),
        "load": str(row["load"]),
        "meal_count": int(row["meal_count"]),
        "updated_at": str(row["updated_at"]),
    }


def save_morning_context(day: str, sleep: str, load: str, meal_count: int) -> None:
    from src.client_profile import plan_user_key

    user_key = plan_user_key()
    if not user_key:
        return

    df = _read_csv(MORNING_CONTEXT_FILE, MORNING_CONTEXT_COLUMNS)
    now = datetime.now().isoformat(timespec="seconds")
    row = {
        "date": day,
        "user_key": user_key,
        "sleep": sleep,
        "load": load,
        "meal_count": str(int(meal_count)),
        "updated_at": now,
    }
    if df.empty:
        out = pd.DataFrame([row])
    else:
        mask = (df["date"] == day) & (df["user_key"] == user_key)
        df = df[~mask]
        out = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(out[MORNING_CONTEXT_COLUMNS], MORNING_CONTEXT_FILE)
