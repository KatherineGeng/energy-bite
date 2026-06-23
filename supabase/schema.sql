-- Energy Bite — Supabase schema (phase 1)
-- Run via scripts/init_supabase.py or Supabase SQL editor.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nickname TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    gender TEXT NOT NULL DEFAULT '',
    age_group TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_nickname_unique UNIQUE (nickname)
);

CREATE TABLE IF NOT EXISTS ingredients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    nutrition_category TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS system_menus (
    menu_id TEXT PRIMARY KEY,
    menu_name TEXT NOT NULL,
    ingredient_ids TEXT NOT NULL DEFAULT '',
    energy_tags TEXT NOT NULL DEFAULT '',
    meal_type TEXT NOT NULL DEFAULT '午餐',
    prep_minutes INTEGER NOT NULL DEFAULT 15,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS user_menus (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    menu_id TEXT NOT NULL,
    menu_name TEXT NOT NULL,
    ingredient_ids TEXT NOT NULL DEFAULT '',
    energy_tags TEXT NOT NULL DEFAULT '',
    meal_type TEXT NOT NULL DEFAULT '午餐',
    prep_minutes INTEGER NOT NULL DEFAULT 15,
    description TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'manual',
    saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, menu_id)
);

CREATE INDEX IF NOT EXISTS idx_user_menus_user ON user_menus (user_id);

CREATE TABLE IF NOT EXISTS daily_meal_plans (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    plan_date DATE NOT NULL,
    breakfast TEXT NOT NULL DEFAULT '',
    lunch TEXT NOT NULL DEFAULT '',
    dinner TEXT NOT NULL DEFAULT '',
    confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    snapshots JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, plan_date)
);

CREATE TABLE IF NOT EXISTS morning_context (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    context_date DATE NOT NULL,
    sleep TEXT NOT NULL DEFAULT '',
    load TEXT NOT NULL DEFAULT '',
    meal_count INTEGER NOT NULL DEFAULT 3,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, context_date)
);

CREATE TABLE IF NOT EXISTS review_logs (
    log_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    menu_id TEXT NOT NULL DEFAULT '',
    taste_score INTEGER,
    operation_score INTEGER,
    mood_score INTEGER,
    energy_score INTEGER,
    is_favorited BOOLEAN NOT NULL DEFAULT FALSE,
    sleep_quality TEXT NOT NULL DEFAULT '',
    brain_body_load TEXT NOT NULL DEFAULT '',
    meal_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_logs_user_date ON review_logs (user_id, log_date);

CREATE TABLE IF NOT EXISTS favorite_dishes (
    fav_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    menu_id TEXT NOT NULL,
    fav_date DATE NOT NULL,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS favorite_menus (
    fav_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    fav_date DATE NOT NULL,
    menu_ids TEXT NOT NULL,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS menu_weights (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    menu_id TEXT NOT NULL,
    base_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    multiplier DOUBLE PRECISION NOT NULL DEFAULT 1,
    final_weight DOUBLE PRECISION NOT NULL DEFAULT 0,
    is_favorited BOOLEAN NOT NULL DEFAULT FALSE,
    log_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, menu_id)
);
