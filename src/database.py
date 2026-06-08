import sqlite3
import threading
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "salut.db"


class Database:
    def __init__(self, path=None):
        self._path = path or DATABASE_PATH
        self._local = threading.local()
        self._connections = []

    def _get_connection(self):
        if not hasattr(self._local, "connection"):
            conn = sqlite3.connect(self._path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.row_factory = sqlite3.Row
            self._local.connection = conn
            self._local.in_transaction = False
            self._connections.append(conn)
        return self._local.connection

    def _get_in_transaction(self):
        if not hasattr(self._local, "in_transaction"):
            self._local.in_transaction = False
        return self._local.in_transaction

    def _set_in_transaction(self, value):
        if not hasattr(self._local, "in_transaction"):
            self._local.in_transaction = False
        self._local.in_transaction = value

    def execute(self, sql, params=None):
        conn = self._get_connection()
        if params:
            conn.execute(sql, params)
        else:
            conn.execute(sql)
        if not self._get_in_transaction():
            conn.commit()

    def begin_transaction(self):
        conn = self._get_connection()
        self._set_in_transaction(True)
        conn.execute("BEGIN")

    def commit_transaction(self):
        conn = self._get_connection()
        conn.commit()
        self._set_in_transaction(False)

    def rollback_transaction(self):
        conn = self._get_connection()
        conn.execute("ROLLBACK")
        self._set_in_transaction(False)

    def fetch_one(self, sql, params=None):
        conn = self._get_connection()
        if params:
            cursor = conn.execute(sql, params)
        else:
            cursor = conn.execute(sql)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(self, sql, params=None):
        conn = self._get_connection()
        if params:
            cursor = conn.execute(sql, params)
        else:
            cursor = conn.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        for conn in self._connections:
            try:
                conn.close()
            except Exception:  # pylint: disable=broad-except
                pass

    def delete(self):
        self.close()
        for suffix in ["", "-wal", "-shm"]:
            self._path.with_name(self._path.name + suffix).unlink(missing_ok=True)
