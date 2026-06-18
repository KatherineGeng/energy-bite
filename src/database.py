"""CSV persistence layer for Energy Bite."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.constants import (
    INGREDIENTS_FILE,
    LOG_FILE,
    MENU_FILE,
    SCORE_MAX,
    SCORE_MIN,
    WEIGHTS_FILE,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data"

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


def load_favorites_dishes() -> pd.DataFrame:
    return _read_csv(FAVORITES_DISHES_FILE, FAVORITES_DISHES_COLUMNS)


def load_favorites_menus() -> pd.DataFrame:
    return _read_csv(FAVORITES_MENUS_FILE, FAVORITES_MENUS_COLUMNS)


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
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    _write_csv(df, FAVORITES_DISHES_FILE)


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
    return menu_id
