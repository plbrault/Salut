from src.database import Database


class TestDatabase:
    def test_init_creates_database(self, tmp_path):
        db = Database(tmp_path / "test.db")
        assert (tmp_path / "test.db").exists()
        db.close()

    def test_wal_mode_enabled(self, tmp_path):
        db = Database(tmp_path / "test.db")
        cursor = db._connection.execute("PRAGMA journal_mode")  # pylint: disable=protected-access
        mode = cursor.fetchone()[0]
        db.close()
        assert mode == "wal"

    def test_execute_creates_table(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute(
            "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"
        )
        cursor = db._connection.execute(  # pylint: disable=protected-access
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_execute_inserts_data(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
        db.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
        row = db.fetch_one("SELECT * FROM test_table")
        assert row["name"] == "test"
        db.close()

    def test_fetch_one_returns_dict(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
        db.execute("INSERT INTO test_table (name) VALUES (?)", ("hello",))
        row = db.fetch_one("SELECT * FROM test_table WHERE name = ?", ("hello",))
        assert isinstance(row, dict)
        assert row["name"] == "hello"
        db.close()

    def test_fetch_one_returns_none_when_empty(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
        row = db.fetch_one("SELECT * FROM test_table")
        assert row is None
        db.close()

    def test_fetch_all_returns_list_of_dicts(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
        db.execute("INSERT INTO test_table (name) VALUES (?)", ("a",))
        db.execute("INSERT INTO test_table (name) VALUES (?)", ("b",))
        rows = db.fetch_all("SELECT * FROM test_table ORDER BY id")
        assert isinstance(rows, list)
        assert len(rows) == 2
        assert rows[0]["name"] == "a"
        assert rows[1]["name"] == "b"
        db.close()

    def test_fetch_all_returns_empty_list(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
        rows = db.fetch_all("SELECT * FROM test_table")
        assert rows == []
        db.close()
