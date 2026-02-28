import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "stylebot.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS profiles (
            user_id           INTEGER PRIMARY KEY REFERENCES users(id),
            style_adjectives  TEXT DEFAULT '[]',
            preferred_colors  TEXT DEFAULT '[]',
            avoided_colors    TEXT DEFAULT '[]',
            preferred_brands  TEXT DEFAULT '[]',
            avoided_brands    TEXT DEFAULT '[]',
            size_tops         TEXT,
            size_bottoms      TEXT,
            size_shoes        TEXT,
            budget_min        INTEGER DEFAULT 0,
            budget_max        INTEGER DEFAULT 500,
            occasions         TEXT DEFAULT '[]',
            fit_preferences   TEXT DEFAULT '[]',
            notes             TEXT DEFAULT '',
            updated_at        TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS wardrobe (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            name         TEXT NOT NULL,
            category     TEXT NOT NULL,
            color        TEXT,
            brand        TEXT,
            condition    TEXT DEFAULT 'good',
            tags         TEXT DEFAULT '[]',
            image_url    TEXT,
            purchase_url TEXT,
            added_at     TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
