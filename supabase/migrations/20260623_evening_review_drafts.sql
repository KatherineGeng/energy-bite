-- Run once in Supabase SQL editor if evening_review_drafts is missing.

CREATE TABLE IF NOT EXISTS evening_review_drafts (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    review_date DATE NOT NULL,
    day_mood INTEGER,
    day_energy INTEGER,
    fav_full_day BOOLEAN NOT NULL DEFAULT FALSE,
    dish_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, review_date)
);
