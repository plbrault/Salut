## Why

Salut currently only supports static HTML cards. Users want live content — RSS feeds are the most common use case for a personal starter page. The project already has `feedparser` and `apscheduler` dependencies, plus a `feed_items` table, so the foundation is in place.

The current plugin interface (`render(options) → str`) is too limited for plugins that need background work. `main.py` hard-codes RSS-specific scheduling logic, violating plugin encapsulation. This change introduces a proper plugin class hierarchy so plugins can own their lifecycle.

## What Changes

- Add abstract `Plugin` base class with `setup(options, database, scheduler, logger)` and `render(options)` methods
- Refactor `html` plugin to use the new class hierarchy
- Add `rss` plugin using the new class hierarchy (fetches feeds, caches images, schedules refresh)
- `main.py` becomes completely plugin-agnostic: instantiates the correct plugin class per card, calls `setup` and `render`
- Cards can specify multiple feeds, a max item count, image fetching, and a cron-based refresh schedule
- Background scheduler fetches feeds periodically and stores items in the database
- On refresh, old items for a card are erased and re-fetched (no complex diffing)
- Images are fetched and cached locally in a `cache/` subfolder, cleared on refresh
- Items are associated with cards via a hash of the card options (not title)

## Capabilities

### New Capabilities

- `rss-plugin`: RSS feed fetching, caching, scheduling, and rendering

### Modified Capabilities

- `card-plugins`: Plugin interface upgraded from function-based to class-based with `Plugin` abstract base class, `setup` lifecycle hook, and `render` method

## Impact

- `src/plugins/rss/` — new plugin directory
- `src/database.py` — add `card_id` and `image_url` columns to `feed_items` table
- `src/main.py` — start APScheduler on startup, add RSS card jobs
- `cache/` — new directory for cached feed images
- `starter.yml` — example RSS card config
- `docs/plugins/` — RSS plugin documentation
- No new dependencies (feedparser and apscheduler already present)
