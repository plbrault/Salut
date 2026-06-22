## Purpose

RSS plugin for fetching and displaying feed items on the starter page.

## Requirements

### Requirement: Plugin abstract base class
The system SHALL provide an abstract `Plugin` base class in `src/plugin.py` with `setup`, `render`, `init_schema`, `validate_options`, `parse_schedule`, and `load_template` methods.

#### Scenario: Plugin class has setup method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `setup(self, cards, database, scheduler, logger)` where `cards` is a list of card dicts

#### Scenario: Plugin class has render method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `render(self, cards) → list[str]` returning a list of HTML strings

#### Scenario: Plugin class has init_schema method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `init_schema(database)` as a static method to create plugin-specific tables

#### Scenario: Plugin class has validate_options method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `validate_options(options, card_idx, filename)` as a static method to validate plugin-specific options

### Requirement: Plugins are loaded as classes
The system SHALL load plugins by importing their class from `src/plugins/<name>/plugin.py` and instantiating it.

#### Scenario: Plugin is instantiated per card
- **WHEN** the system processes a card with `plugin: rss`
- **THEN** it imports `RssPlugin` from `src.plugins.rss.plugin` and creates an instance

#### Scenario: Plugin setup is called at startup
- **WHEN** the server starts and cards use a plugin
- **THEN** the system calls `setup_plugin(plugin_name, cards, database, scheduler, language, card_ids)`
- **AND** `setup_plugin` creates a single instance and calls `instance.setup(cards, database, scheduler, logger)`

#### Scenario: Plugin render is called on request
- **WHEN** the index page is requested
- **THEN** the system calls `plugin_instance.render(cards)` with all cards of that plugin type

### Requirement: HTML plugin uses Plugin class
The system SHALL provide an `HtmlPlugin` class extending `Plugin` that renders HTML from options.

#### Scenario: HTML plugin renders content
- **WHEN** a card has `plugin: html` with `options: { html: "<p>Hello</p>" }`
- **THEN** the rendered card contains the HTML content

#### Scenario: HTML plugin setup is a no-op
- **WHEN** `HtmlPlugin.setup()` is called
- **THEN** no action is taken (HTML is static)

### Requirement: RSS plugin uses Plugin class
The system SHALL provide an `RssPlugin` class extending `Plugin` that fetches RSS feeds and renders items.

#### Scenario: RSS plugin setup registers global tick
- **WHEN** `RssPlugin.setup()` is called with a list of cards
- **THEN** it stores card configs and registers a single cron job (the "tick") with the scheduler, evaluated every 5 minutes
- **AND** it does NOT register per-card cron jobs

#### Scenario: RSS plugin renders items from database
- **WHEN** a card has `plugin: rss` with items in the database
- **THEN** the rendered card contains a list of feed items

#### Scenario: RSS plugin owns its database schema
- **WHEN** `RssPlugin.setup_database(database)` is called
- **THEN** it creates the `feed_items` table if it does not exist

#### Scenario: RSS plugin owns its database queries
- **WHEN** `RssPlugin` needs to read or write feed items
- **THEN** it uses private methods on the instance that call `self._database.execute()`, `self._database.fetch_all()`, etc.

#### Scenario: RSS plugin validates options
- **WHEN** `RssPlugin.validate_options()` is called
- **THEN** it checks that `feeds` is a non-empty list and `schedule` is a valid cron expression

#### Scenario: RSS plugin renders items using template
- **WHEN** `RssPlugin.render()` is called
- **THEN** it renders items using a Jinja2 template at `src/plugins/rss/template.html`

#### Scenario: RSS plugin displays feed title as source
- **WHEN** an RSS feed provides a channel title
- **THEN** the rendered item displays the feed title as the source instead of the domain name

#### Scenario: RSS plugin falls back to domain when no feed title
- **WHEN** an RSS feed does not provide a channel title
- **THEN** the rendered item displays the domain name (without `www.`) as the source

#### Scenario: RSS plugin sorts items without dates to the end
- **WHEN** some feed items have no `published` date
- **THEN** items with dates are sorted most recent first, and items without dates appear at the end

#### Scenario: RSS plugin fetches feeds atomically
- **WHEN** `RssPlugin._fetch_feeds()` is called
- **THEN** it first performs all network I/O (fetch feeds, sort, deduplicate, download images), then begins a database transaction, then performs DELETE and INSERT operations, then commits the transaction

#### Scenario: RSS plugin rolls back on error
- **WHEN** an error occurs during the database write phase of `_fetch_feeds()`
- **THEN** the transaction is rolled back using `rollback_transaction()`, and the per-thread transaction state is reset

#### Scenario: RSS plugin enforces unique feed items per card
- **WHEN** a feed item with a duplicate `link` is inserted for a card
- **THEN** the database constraint prevents the duplicate from being stored

### Requirement: RSS plugin deduplicates feed items by link
The system SHALL deduplicate feed items by both `link` URL and `title`. When multiple items share the same `link` URL, only one instance is kept. When multiple items from different feeds share the same `title` (exact match, after stripping whitespace), only one instance is kept, retaining the item from the feed with higher precedence (earlier in the `feeds` config list).

#### Scenario: RSS plugin deduplicates feed items by link
- **WHEN** multiple feeds return items with the same `link` URL
- **THEN** only one instance of each item is kept (the first after sorting by published date descending)

#### Scenario: RSS plugin deduplicates feed items by title across feeds
- **WHEN** multiple feeds return items with the same `title` (exact match) but different `link` URLs
- **THEN** only one instance is kept, retaining the item from the feed that appears earlier in the `feeds` config list

#### Scenario: RSS plugin preserves items with different titles and links
- **WHEN** two feed items have different `title` values and different `link` URLs
- **THEN** both items are kept

#### Scenario: RSS plugin title dedup is case-sensitive
- **WHEN** two feed items have titles that differ only in casing (e.g., "Hello World" vs "hello world")
- **THEN** they are treated as different items and both are kept

### Requirement: RSS plugin fetches feeds atomically
The system SHALL wrap the DELETE and INSERT operations in a database transaction to prevent race conditions. Image cache files SHALL be downloaded using `ImageCache` before the transaction commits. Old cache files SHALL only be deleted after the transaction commits successfully via `ImageCache.cleanup_orphans`. Cache filenames SHALL be derived from a SHA-256 hash of the remote image URL rather than the item's positional index.

#### Scenario: RSS plugin writes new images before committing transaction
- **WHEN** `RssPlugin._fetch_feeds()` is called with `fetch_images=True`
- **THEN** new image files are written to disk before the database transaction is committed

#### Scenario: RSS plugin deletes orphaned cache files after commit
- **WHEN** the database transaction commits successfully
- **THEN** any cache files that are not referenced by the current database rows are deleted via `ImageCache.cleanup_orphans`

#### Scenario: RSS plugin preserves old cache files on refresh failure
- **WHEN** an exception occurs during feed fetching and the transaction is rolled back
- **THEN** old cache files remain on disk and are not deleted

#### Scenario: RSS plugin uses hash-based cache filenames
- **WHEN** an image is downloaded and cached
- **THEN** the filename is derived from `ImageCache.hash_filename` using the remote image URL

#### Scenario: RSS plugin same image URL produces same filename
- **WHEN** the same remote image URL appears in multiple refresh cycles
- **THEN** the cached filename is identical across refreshes

#### Scenario: RSS plugin different image URLs produce different filenames
- **WHEN** two different remote image URLs are cached
- **THEN** they produce different cache filenames

### Requirement: Plugin setup is called once per plugin type
The system SHALL call `setup_plugin` once for each plugin type, passing all cards using that plugin as a list. The `setup_plugin` function SHALL create a single plugin instance, store the `card_ids` map on it, and call `setup(cards, database, scheduler, logger)`. The plugin iterates over the card list internally, handling scheduling and data fetching.

#### Scenario: Multiple cards with same plugin
- **WHEN** two cards both have `plugin: rss`
- **THEN** the system calls `setup_plugin` once for the `rss` plugin type, passing both cards as a list
- **AND** the plugin registers a single global tick and stores card configs

#### Scenario: Card IDs map is stored on instance
- **WHEN** `setup_plugin` is called with a `card_ids` map
- **THEN** the map is stored on the plugin instance as `instance._card_ids` before `setup` is called
- **AND** plugins can access it via `self._card_ids` to resolve cross-card references

### Requirement: Main is plugin-agnostic
`main.py` SHALL NOT contain any plugin-specific logic. It SHALL group cards by plugin type, call `setup_plugin` once per plugin type with the full card list, and call `render` with the full card list. `main.py` SHALL pre-compute all card IDs (from explicit `card_id` fields or by hashing options) and pass the resulting map to `setup_plugin`, so plugins receive resolved card IDs without computing them themselves.

#### Scenario: No plugin imports in main
- **WHEN** `main.py` is loaded
- **THEN** it does not import from any specific plugin module (e.g., `src.plugins.rss`)

#### Scenario: Plugin-agnostic card processing
- **WHEN** the server starts
- **THEN** `main.py` groups cards by plugin type, calls `setup_plugin` once per type, and calls `render` once per type

#### Scenario: Main computes card IDs for all cards
- **WHEN** the server starts and processes the card list
- **THEN** `main.py` computes a card ID for each card (using the explicit `card_id` if present, otherwise by hashing options) and passes the full `card_ids` map to `setup_plugin`

### Requirement: Config validation is plugin-agnostic
Config validation SHALL delegate plugin-specific option validation to each plugin's `validate_options` method rather than hardcoding plugin-specific logic.

#### Scenario: Config validates plugin options via plugin class
- **WHEN** a card has a valid plugin name
- **THEN** config validation calls `plugin_class.validate_options(options, card_idx, filename)`

#### Scenario: Unknown plugin skips option validation
- **WHEN** a card has an unknown plugin name
- **THEN** config validation skips plugin-specific option validation

### Requirement: RSS plugin supports distinct_from option
The system SHALL accept an optional `distinct_from` field in the RSS card's options. When provided, the value SHALL be a list of `card_id` strings referencing other RSS cards. During the global tick, due cards SHALL be topologically sorted so that when a dependency and its dependent are both due in the same tick, the dependency is refreshed first. A card's dependency SHALL NOT be refreshed more often than its own schedule — dependents use whatever data the dependency currently has in the database. Cards SHALL exclude feed items that match items in any referenced card (by `link` URL and `title`). Excluded items SHALL NOT be stored in the database for this card.

#### Scenario: Card filters items from multiple referenced cards at fetch time
- **WHEN** card A has `distinct_from: ["card-b", "card-c"]` and card B has items with links [X, Y] and card C has items with links [Z, W]
- **THEN** card A's database contains no items with links X, Y, Z, or W after fetching

#### Scenario: Filtering by title match
- **WHEN** card A has `distinct_from: ["card-b"]` and card B has an item with title "Breaking News" and a different link URL
- **THEN** card A excludes any fetched item with the same title "Breaking News"

#### Scenario: Referenced cards have priority
- **WHEN** card A has `distinct_from: ["card-b"]` and both cards share items with links [X, Y]
- **THEN** card B retains items X and Y in its database, and card A does not store them

#### Scenario: max_items applies after filtering
- **WHEN** a card has `max_items: 5` and `distinct_from: ["card-b"]` and 3 items are filtered out
- **THEN** the card stores and displays up to 5 items (not 5 minus the filtered count)

#### Scenario: No filtering when distinct_from is absent
- **WHEN** an RSS card has no `distinct_from` option
- **THEN** all feed items are fetched and stored normally

#### Scenario: Empty distinct_from array
- **WHEN** a card has `distinct_from: []`
- **THEN** no items are filtered and all items are fetched normally

#### Scenario: Non-existent referenced card_id
- **WHEN** a card has `distinct_from: ["nonexistent"]` and no card with that card_id exists
- **THEN** no items are filtered for that entry and remaining items are fetched normally

#### Scenario: Tick orders simultaneous refreshes by dependency
- **WHEN** the global tick fires and both card A and card B are due, with card B having `distinct_from: ["card-a"]`
- **THEN** card A is refreshed first, then card B

#### Scenario: Dependency is not refreshed more often than its schedule
- **WHEN** card B is due with `distinct_from: ["card-a"]` and card A is NOT due by its own schedule
- **THEN** card A is NOT refreshed — card B uses card A's existing data in the database

#### Scenario: Dependency cycle is rejected at validation
- **WHEN** config has card A with `distinct_from: ["card-b"]` and card B with `distinct_from: ["card-a"]`
- **THEN** `validate_options` raises a configuration error
