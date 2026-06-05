import sqlite3

from app.database import init_database


class TestDatabase:
    def test_init_creates_database(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "test.db")
        init_database()
        assert (tmp_path / "test.db").exists()

    def test_feed_items_table_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "test.db")
        init_database()
        conn = sqlite3.connect(tmp_path / "test.db")
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feed_items'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_wal_mode_enabled(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "test.db")
        init_database()
        conn = sqlite3.connect(tmp_path / "test.db")
        cursor = conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        conn.close()
        assert mode == "wal"

    def test_feed_items_schema(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.database.DATABASE_PATH", tmp_path / "test.db")
        init_database()
        conn = sqlite3.connect(tmp_path / "test.db")
        cursor = conn.execute("PRAGMA table_info(feed_items)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        expected = {"id", "url", "title", "link", "published", "feed_url", "fetched_at"}
        assert expected.issubset(columns)
