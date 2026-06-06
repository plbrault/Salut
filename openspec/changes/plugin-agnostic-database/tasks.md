## 1. Database class

- [x] 1.1 Rewrite `src/database.py` as a `Database` class with `execute()`, `fetch_one()`, `fetch_all()` methods
- [x] 1.2 Remove `init_database()`, `delete_feed_items()`, `insert_feed_item()`, `get_feed_items()` from `database.py`
- [x] 1.3 Update `src/main.py` to create a `Database` instance and pass it to `setup_card`

## 2. Plugin base class

- [x] 2.1 Add abstract `setup_database(database)` static method to `Plugin` in `src/plugin.py`
- [x] 2.2 Implement no-op `setup_database` in `HtmlPlugin`

## 3. RSS plugin database ownership

- [x] 3.1 Add `setup_database` to `RssPlugin` — create `feed_items` table with all columns
- [x] 3.2 Move `delete_feed_items` logic to a private method on `RssPlugin`
- [x] 3.3 Move `insert_feed_item` logic to a private method on `RssPlugin`
- [x] 3.4 Move `get_feed_items` logic to a private method on `RssPlugin`
- [x] 3.5 Update `_fetch_feeds` and `render` to use the new private methods via `self._database`

## 4. Tests

- [x] 4.1 Update `test_database.py` to test the new `Database` class
- [x] 4.2 Update `test_plugins.py` — fix any broken imports or API calls
- [x] 4.3 Verify all 85 tests pass

## 5. Cleanup

- [x] 5.1 Run `pipenv run pylint` and fix any issues
