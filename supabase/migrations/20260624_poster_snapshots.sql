-- Generated poster PNG storage (per user per day)
CREATE TABLE IF NOT EXISTS poster_snapshots (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    poster_date DATE NOT NULL,
    png_data BYTEA NOT NULL,
    menu_ids TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, poster_date)
);

CREATE INDEX IF NOT EXISTS idx_poster_snapshots_user_date ON poster_snapshots (user_id, poster_date DESC);
