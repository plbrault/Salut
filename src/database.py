import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "salut.db"


def get_database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


def init_database():
    connection = get_database()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS feed_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            published TEXT,
            feed_url TEXT NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()
    connection.close()
