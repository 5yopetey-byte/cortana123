"""
Initialize SQLite databases for memory, notes, history.
"""
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).parent
MEMORY_DB = DB_DIR / "memory.db"
NOTES_DB = DB_DIR / "notes.db"
HISTORY_DB = DB_DIR / "history.db"


def init_memory():
    with sqlite3.connect(MEMORY_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def init_notes():
    with sqlite3.connect(NOTES_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                body TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def init_history():
    with sqlite3.connect(HISTORY_DB) as conn:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def main():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    init_memory()
    init_notes()
    init_history()
    print("Databases initialized.")


if __name__ == "__main__":
    main()
