import threading
import time

from src.database import Database


class TestDatabase:
    def test_init_creates_database(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db._get_connection()  # pylint: disable=protected-access
        assert (tmp_path / "test.db").exists()
        db.close()

    def test_wal_mode_enabled(self, tmp_path):
        db = Database(tmp_path / "test.db")
        conn = db._get_connection()  # pylint: disable=protected-access
        cursor = conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        db.close()
        assert mode == "wal"

    def test_execute_creates_table(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute(
            "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"
        )
        conn = db._get_connection()  # pylint: disable=protected-access
        cursor = conn.execute(
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


class TestDatabaseConcurrency:
    def test_concurrent_threads_can_begin_commit_transactions(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")

        errors = []

        def thread_work(thread_name):
            try:
                db.begin_transaction()
                db.execute("INSERT INTO test_table (name) VALUES (?)", (thread_name,))
                db.commit_transaction()
            except Exception as e:  # pylint: disable=broad-except
                errors.append(e)

        t1 = threading.Thread(target=thread_work, args=("t1",))
        t2 = threading.Thread(target=thread_work, args=("t2",))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        assert not errors, f"Got errors: {errors}"

        rows = db.fetch_all("SELECT name FROM test_table ORDER BY name")
        names = [r["name"] for r in rows]
        assert "t1" in names
        assert "t2" in names
        db.close()

    def test_auto_commit_not_affected_by_other_thread_transaction(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")

        barrier = threading.Barrier(2)
        errors = []

        def thread_a():
            try:
                db.begin_transaction()
                barrier.wait()
                time.sleep(0.1)
                db.commit_transaction()
            except Exception as e:  # pylint: disable=broad-except
                errors.append(e)

        def thread_b():
            try:
                barrier.wait()
                db.execute("INSERT INTO test_table (name) VALUES (?)", ("auto",))
            except Exception as e:  # pylint: disable=broad-except
                errors.append(e)

        t1 = threading.Thread(target=thread_a)
        t2 = threading.Thread(target=thread_b)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        assert not errors, f"Got errors: {errors}"

        rows = db.fetch_all("SELECT name FROM test_table")
        assert any(r["name"] == "auto" for r in rows)
        db.close()

    def test_rollback_resets_transaction_state(self, tmp_path):
        db = Database(tmp_path / "test.db")
        db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")

        db.begin_transaction()
        db.execute("INSERT INTO test_table (name) VALUES (?)", ("should_rollback",))
        db.rollback_transaction()

        rows = db.fetch_all("SELECT * FROM test_table")
        assert rows == []
        assert not db._get_in_transaction()  # pylint: disable=protected-access
        db.close()

    def test_background_thread_connections_use_wal_and_row_factory(self, tmp_path):
        db = Database(tmp_path / "test.db")
        results = {}

        def thread_work():
            conn = db._get_connection()  # pylint: disable=protected-access
            cursor = conn.execute("PRAGMA journal_mode")
            results["wal"] = cursor.fetchone()[0]
            results["row_factory"] = conn.row_factory
            db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
            db.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
            row = db.fetch_one("SELECT * FROM test_table")
            results["row_is_dict"] = isinstance(row, dict)

        t = threading.Thread(target=thread_work)
        t.start()
        t.join()

        assert results.get("wal") == "wal"
        assert results.get("row_factory") is not None
        assert results.get("row_is_dict") is True
        db.close()
