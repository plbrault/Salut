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
    try:
        connection.execute("ALTER TABLE feed_items ADD COLUMN card_id TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        connection.execute("ALTER TABLE feed_items ADD COLUMN image_url TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        connection.execute("ALTER TABLE feed_items ADD COLUMN feed_title TEXT")
    except sqlite3.OperationalError:
        pass
    connection.commit()
    connection.close()


def delete_feed_items(card_id):
    connection = get_database()
    connection.execute("DELETE FROM feed_items WHERE card_id = ?", (card_id,))
    connection.commit()
    connection.close()


def insert_feed_item(**kwargs):
    connection = get_database()
    connection.execute(
        """
        INSERT INTO feed_items (card_id, url, title, link, published, feed_url, image_url, feed_title)
        VALUES (:card_id, :url, :title, :link, :published, :feed_url, :image_url, :feed_title)
        """,
        kwargs,
    )
    connection.commit()
    connection.close()


def get_feed_items(card_id):
    connection = get_database()
    connection.row_factory = sqlite3.Row
    cursor = connection.execute(
        "SELECT * FROM feed_items WHERE card_id = ? ORDER BY published DESC",
        (card_id,),
    )
    items = [dict(row) for row in cursor.fetchall()]
    connection.close()
    return items
