## Why

`src/database.py` contains RSS-specific code (feed_items table, insert/delete/query functions). This violates the project's plugin-agnostic architecture — anything outside `plugins/` should not contain plugin-specific logic. Adding a new plugin with its own data would require modifying `database.py` again.

## What Changes

- Replace the module-level database functions with a `Database` class that exposes generic query methods (`execute`, `fetch_one`, `fetch_all`)
- Add an abstract `setup_database` static method to the `Plugin` class — each plugin implements this to create its own tables via migrations
- Move RSS-specific database operations (table creation, insert, delete, query) into `RssPlugin.setup_database` and instance methods on `RssPlugin`
- `database.py` becomes a thin wrapper around sqlite3 with no plugin knowledge

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `rss-plugin`: Plugin now owns its database schema and queries via `setup_database` and instance methods
- `card-plugins`: Plugin abstract base class gains `setup_database` method

## Impact

- `src/database.py` — rewritten as generic `Database` class
- `src/plugin.py` — add abstract `setup_database` static method
- `src/plugins/rss/plugin.py` — move table creation and queries here
- `src/plugins/html/plugin.py` — implement no-op `setup_database`
- `src/main.py` — pass `Database` instance to `setup_card`, call each plugin's `setup_database`
- `tests/test_plugins.py`, `tests/test_database.py` — update for new API
