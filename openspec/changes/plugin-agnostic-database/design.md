## Context

`src/database.py` currently contains RSS-specific code: the `feed_items` table schema, `insert_feed_item`, `delete_feed_items`, and `get_feed_items` functions. This means any new plugin that needs persistence must modify `database.py`, violating the plugin-agnostic architecture. The `Database` class should be a generic query layer; each plugin owns its schema and queries.

## Goals / Non-Goals

**Goals:**
- `src/database.py` becomes a generic `Database` class with no plugin knowledge
- Each plugin owns its database schema via `setup_database` and its own query methods
- `main.py` passes a `Database` instance to plugins (no changes to main's plugin-agnostic nature)

**Non-Goals:**
- Changing the database engine (stays sqlite3)
- Adding connection pooling or async database support
- Refactoring the existing RSS plugin behavior (just moving code)

## Decisions

### Database class API

The `Database` class will expose:
- `execute(sql, params)` — run a write query (CREATE TABLE, INSERT, DELETE)
- `fetch_one(sql, params)` — return a single row as dict
- `fetch_all(sql, params)` — return all rows as list of dicts

**Why not pass raw connections?** A class allows us to swap implementations later (e.g., async, different DB) without changing every plugin. It also keeps connection management in one place.

### Plugin.setup_database static method

Each plugin implements `setup_database(database)` as a static method. Called once at startup before `setup()`. The RSS plugin creates `feed_items` table here; HTML plugin is a no-op.

**Why static?** Schema setup doesn't need instance state — it's a one-time migration. Making it static keeps it simple and explicit.

### RSS queries move to RssPlugin

`insert_feed_item`, `delete_feed_items`, `get_feed_items` become private methods on `RssPlugin`. They use `self._database` which is passed during `setup()`.

## Risks / Trade-offs

- [Tests need updating] → Update `test_database.py` to test the new `Database` class, update `test_plugins.py` for new plugin API
- [One-time migration] → `init_database()` becomes `Database()` constructor or a simple `CREATE TABLE IF NOT EXISTS` for any shared tables (none expected)
