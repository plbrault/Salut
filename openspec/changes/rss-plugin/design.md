## Context

Salut is a self-hosted starter page with a plugin-based card system. The current plugin interface is function-based: each plugin exports a `render(options) → HTML string` function loaded via `importlib`. The only implementation is the `html` plugin.

Users want live content — RSS feeds being the primary use case. The project already has `feedparser` and `apscheduler` dependencies plus a `feed_items` table in SQLite. However, the current function-based plugin interface cannot support plugins that need background work (like periodic feed fetching). Currently `main.py` hard-codes RSS-specific scheduling logic, violating plugin encapsulation.

## Goals / Non-Goals

**Goals:**
- Abstract `Plugin` base class with `setup` and `render` lifecycle methods
- RSS plugin that fetches multiple feeds, caches items in the database, and renders them as HTML
- Cron-based refresh schedule per card, owned by the plugin
- `main.py` completely plugin-agnostic
- HTML plugin migrated to the new class hierarchy

**Non-Goals:**
- Real-time push updates (polling only)
- Feed discovery (users provide feed URLs)
- Deduplication across cards (each card is independent)
- Other feed formats (Atom, JSON Feed) — feedparser handles these already
- Plugin hot-reloading

## Decisions

### 1. Plugin class hierarchy

**Decision:** Each plugin defines a class extending an abstract `Plugin` base class. The class lives in a dedicated file within the plugin directory. The `__init__.py` only imports the class.

```
src/plugins/
├── __init__.py          # generic load/setup/render functions
├── base.py              # abstract Plugin class
├── html/
│   ├── __init__.py      # from src.plugins.html.plugin import HtmlPlugin
│   └── plugin.py        # class HtmlPlugin(Plugin)
└── rss/
    ├── __init__.py      # from src.plugins.rss.plugin import RssPlugin
    └── plugin.py        # class RssPlugin(Plugin)
```

**Rationale:**
- Separation of concerns: `__init__.py` is a re-export shim, logic lives in `plugin.py`
- `plugin.py` avoids circular imports and keeps `__init__.py` clean
- Consistent structure across all plugins

### 2. Plugin abstract interface

**Decision:** The `Plugin` base class defines two methods:

```python
from abc import ABC, abstractmethod

class Plugin(ABC):
    @abstractmethod
    def setup(self, options, database, scheduler, logger):
        """Initialize the plugin for a card. Called once at startup."""

    @abstractmethod
    def render(self, options):
        """Return HTML string for the card."""
```

**Parameters for `setup`:**
- `options`: the card's `options` dict from config
- `database`: the database module (for `insert_feed_item`, `get_feed_items`, etc.)
- `scheduler`: the APScheduler `BackgroundScheduler` instance
- `logger`: a `logging.Logger` namespaced to the plugin

**Rationale:**
- `setup` receives dependencies via injection, not module-level imports
- Plugins don't call `get_database()` directly — they use the injected `database`
- `scheduler` is available for plugins that need background work (RSS); HTML ignores it
- `logger` gives each plugin its own logging namespace

### 3. Card identifier in database

**Decision:** Use a SHA-256 hash of the card's options dict (excluding `title`) as `card_id`.

```python
import hashlib, json
card_id = hashlib.sha256(json.dumps(options, sort_keys=True).encode()).hexdigest()[:16]
```

**Rationale:**
- Title is not unique — two cards can have the same title with different feeds
- Options hash uniquely identifies the card's configuration
- Short hash (16 chars) is sufficient for a single-user app

### 4. Database schema changes

**Decision:** Add `card_id` and `image_url` columns to the existing `feed_items` table.

```sql
CREATE TABLE IF NOT EXISTS feed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    published TEXT,
    feed_url TEXT NOT NULL,
    image_url TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Refresh strategy

**Decision:** On each refresh, delete all items for a card and re-fetch from scratch.

**Rationale:**
- Simple to implement — no diffing or update logic
- Feeds are small (typically <100 items)
- Self-hosted app — no concern about brief empty states

### 6. Image caching

**Decision:** Fetch images to `cache/rss/<card_id>/` directory. On refresh, delete the card's cache subfolder before re-fetching.

**Rationale:**
- Local caching avoids hotlinking issues
- Card-specific subfolder makes cleanup trivial
- `cache/` is gitignored

### 7. Scheduler integration

**Decision:** Use APScheduler's `CronTrigger` with standard cron syntax. Each RSS plugin instance registers its own job via the injected `scheduler`.

```python
def setup(self, options, database, scheduler, logger):
    cron = CronTrigger.from_crontab(options["refresh"])
    scheduler.add_job(self._refresh, trigger=cron, args=[options], id=self._card_id)
    self._refresh(options)  # initial fetch
```

**Rationale:**
- APScheduler already a dependency
- Plugin owns its scheduling logic — main.py is unaware
- In-process scheduler is simple for a single-user app

### 8. max_items semantics

**Decision:** `max_items` is the total across all feeds in the card. After fetching all feeds, sort by published date descending and keep only the top `max_items`.

### 9. Feed fetching with timeout

**Decision:** Use `requests.get(url, timeout=10)` to fetch feed content, then pass to `feedparser.parse(content)`. Never call `feedparser.parse(url)` directly.

**Rationale:**
- `feedparser.parse(url)` makes its own HTTP request with no timeout
- Can hang indefinitely on unreachable feeds
- Using `requests` with a timeout prevents startup blocking

## Risks / Trade-offs

- **Feed downtime** → Items for that feed are skipped. Other feeds still work.
- **Config changes** → Changing card options changes the hash, so old items are orphaned. Harmless.
- **Scheduler in-process** → If the app crashes, scheduled fetches stop. Items persist in DB, next startup re-fetches.
- **Setup called at startup** → Each plugin's `setup` runs synchronously during startup. RSS plugin fetches feeds in `setup`, which can be slow with many feeds. Mitigated by using `requests` with timeouts.
