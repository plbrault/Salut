import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent.parent / "salut.db"


class Database:
    def __init__(self, path=None):
        self._path = path or DATABASE_PATH
        self._connection = sqlite3.connect(self._path, check_same_thread=False)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.row_factory = sqlite3.Row

    def execute(self, sql, params=None):
        if params:
            self._connection.execute(sql, params)
        else:
            self._connection.execute(sql)
        self._connection.commit()

    def fetch_one(self, sql, params=None):
        if params:
            cursor = self._connection.execute(sql, params)
        else:
            cursor = self._connection.execute(sql)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(self, sql, params=None):
        if params:
            cursor = self._connection.execute(sql, params)
        else:
            cursor = self._connection.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self._connection.close()
