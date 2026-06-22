"""Shared enums and mapping tables for Energy Bite."""

from __future__ import annotations

# Bump this on every deploy so users can verify Streamlit Cloud picked up the build.
APP_VERSION = "4.8.1"

GENDER_OPTIONS = ["女", "男", "其他"]
AGE_GROUP_OPTIONS = ["40岁以下", "40-49岁", "50-59岁", "60岁及以上"]

# 每日前 N 次「生成/换套」走菜品库，第 N+1 次起走 AI（若已配置 API）
LIBRARY_GEN_MAX = 3

# Canonical nutrition categories for radar chart (7 axes)
NUTRITION_CATEGORIES = [
    "植物雌激素",
    "谷物杂粮",
    "蛋白质",
    "优质脂肪",
    "膳食纤维",
    "高钙",
    "水果",
]

# Extended tags in seed data map to canonical categories for radar aggregation
NUTRITION_ALIAS = {
    "Omega-3": "优质脂肪",
    "维生素": "膳食纤维",
}

SLEEP_OPTIONS = ["很好", "良好", "一般", "较差"]
LOAD_OPTIONS = ["低", "中等", "高"]
MEAL_COUNT_OPTIONS = [1, 2, 3]

MEAL_TYPES = ["早餐", "午餐", "晚餐", "加餐"]

ENERGY_TAG_POOL = [
    "抗炎",
    "稳糖",
    "高抗氧化",
    "补脑",
    "稳情绪",
    "高纤维",
    "补钙",
    "轻断食友好",
    "快速供能",
    "肠脑舒缓",
    "脑力续航",
    "降胆固醇",
    "平稳褪黑素",
    "雌激素补充",
]

# Morning input → preferred energy tag keywords for scoring boost
SLEEP_TAG_BOOST = {
    "较差": ["稳情绪", "肠脑舒缓", "平稳褪黑素", "雌激素补充"],
    "一般": ["稳情绪", "肠脑舒缓"],
    "良好": ["高抗氧化", "脑力续航"],
    "很好": ["轻断食友好", "快速供能"],
}

LOAD_TAG_BOOST = {
    "高": ["补脑", "稳糖", "脑力续航", "快速供能"],
    "中等": ["稳糖", "高抗氧化", "脑力续航"],
    "低": ["高抗氧化", "轻断食友好", "肠脑舒缓"],
}

# State multiplier lookup: rounded half-step average of mood + energy
MULTIPLIER_MAP = {
    1.0: 0.8,
    1.5: 0.8,
    2.0: 0.9,
    2.5: 0.9,
    3.0: 1.0,
    3.5: 1.0,
    4.0: 1.1,
    4.5: 1.1,
    5.0: 1.2,
}

DATA_DIR = "data"
INGREDIENTS_FILE = "ingredients_db.csv"
MENU_FILE = "menu_db.csv"
LOG_FILE = "log_db.csv"
WEIGHTS_FILE = "menu_weights.csv"
MORNING_CONTEXT_FILE = "morning_context.csv"
DAILY_PLAN_FILE = "daily_meal_plans.csv"

SCORE_MIN = 1
SCORE_MAX = 5

POSTER_WIDTH = 1080
POSTER_HEIGHT = 1920
