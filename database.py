import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "stylebot.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _migrate_profiles(conn):
    """Add new columns to existing profiles table (safe to re-run)."""
    new_columns = [
        ("gender", "TEXT"),
        ("age", "INTEGER"),
        ("climate", "TEXT"),
        ("onboarded", "INTEGER DEFAULT 0"),
        ("style_quiz", "TEXT DEFAULT '[]'"),
        ("style_vector", "TEXT DEFAULT '{}'"),
    ]
    for col_name, col_type in new_columns:
        try:
            conn.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass  # column already exists


def _migrate_wardrobe(conn):
    """Add local_image_path column to wardrobe table (safe to re-run)."""
    try:
        conn.execute("ALTER TABLE wardrobe ADD COLUMN local_image_path TEXT")
    except Exception:
        pass  # column already exists


def _migrate_feedback(conn):
    """Add enriched metadata columns to recommendation_feedback (safe to re-run)."""
    new_columns = [
        ("price", "TEXT"),
        ("category", "TEXT"),
        ("seller", "TEXT"),
        ("color", "TEXT"),
        ("search_query", "TEXT"),
        ("image_url", "TEXT"),
    ]
    for col_name, col_type in new_columns:
        try:
            conn.execute(f"ALTER TABLE recommendation_feedback ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass  # column already exists


def _migrate_vector_refinement(conn):
    """Add vector refinement columns to profiles (safe to re-run)."""
    new_columns = [
        ("feedback_vector", "TEXT DEFAULT '{}'"),
        ("refined_style_vector", "TEXT DEFAULT '{}'"),
        ("feedback_vector_count", "INTEGER DEFAULT 0"),
    ]
    for col_name, col_type in new_columns:
        try:
            conn.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass  # column already exists


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
            gender            TEXT,
            age               INTEGER,
            climate           TEXT,
            onboarded         INTEGER DEFAULT 0,
            style_quiz        TEXT DEFAULT '[]',
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

        CREATE TABLE IF NOT EXISTS recommendation_feedback (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL REFERENCES users(id),
            product_title TEXT NOT NULL,
            feedback      TEXT NOT NULL,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS conversation_summaries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            summary         TEXT NOT NULL,
            messages_up_to  INTEGER NOT NULL,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS outfits (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            name       TEXT NOT NULL,
            occasion   TEXT,
            season     TEXT,
            notes      TEXT DEFAULT '',
            image_url  TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS outfit_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            outfit_id   INTEGER NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
            wardrobe_id INTEGER NOT NULL REFERENCES wardrobe(id),
            layer_order INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    _migrate_profiles(conn)
    _migrate_wardrobe(conn)
    _migrate_feedback(conn)
    _migrate_vector_refinement(conn)
    conn.commit()
    conn.close()


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
