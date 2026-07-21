-- PromptSphere database schema (SQLite)

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS prompts;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'buyer' CHECK (role IN ('buyer', 'creator')),
    bio           TEXT DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE prompts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id    INTEGER NOT NULL,
    title         TEXT NOT NULL,
    description   TEXT NOT NULL,
    category      TEXT NOT NULL,
    target_model  TEXT NOT NULL,
    price         REAL NOT NULL CHECK (price >= 0),
    content       TEXT NOT NULL,      -- full prompt text, only revealed after purchase
    preview       TEXT NOT NULL,      -- short teaser shown to everyone
    sales_count   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE purchases (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id      INTEGER NOT NULL,
    prompt_id     INTEGER NOT NULL,
    price_paid    REAL NOT NULL,
    purchased_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    UNIQUE (buyer_id, prompt_id)
);

CREATE TABLE reviews (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id     INTEGER NOT NULL,
    buyer_id      INTEGER NOT NULL,
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment       TEXT DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (prompt_id, buyer_id)
);

CREATE INDEX idx_prompts_category ON prompts(category);
CREATE INDEX idx_prompts_creator ON prompts(creator_id);
CREATE INDEX idx_purchases_buyer ON purchases(buyer_id);
CREATE INDEX idx_reviews_prompt ON reviews(prompt_id);
