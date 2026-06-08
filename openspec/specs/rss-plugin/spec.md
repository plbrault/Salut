## Purpose

RSS plugin for fetching and displaying feed items on the starter page.

## Requirements

### Requirement: Plugin abstract base class
The system SHALL provide an abstract `Plugin` base class in `src/plugin.py` with `setup`, `render`, `init_schema`, `validate_options`, `parse_schedule`, and `load_template` methods.

#### Scenario: Plugin class has setup method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `setup(self, options, database, scheduler, logger)`

#### Scenario: Plugin class has render method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `render(self, options) → str` returning an HTML string

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
- **WHEN** the server starts and a card has a plugin
- **THEN** the system calls `plugin_instance.setup(options, database, scheduler, logger)`

#### Scenario: Plugin render is called on request
- **WHEN** the index page is requested
- **THEN** the system calls `plugin_instance.render(options)` for each card

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

#### Scenario: RSS plugin setup fetches feeds and schedules refresh
- **WHEN** `RssPlugin.setup()` is called with valid options
- **THEN** it fetches feeds, stores items in the database, and registers a cron job with the scheduler

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

### Requirement: Each card gets its own setup
The system SHALL call `setup_card` for every card, even when multiple cards use the same plugin. Each card requires its own feed fetching and scheduler registration.

#### Scenario: Multiple cards with same plugin
- **WHEN** two cards both have `plugin: rss`
- **THEN** the system calls `setup_card` for each card independently, and each card fetches its own feeds

### Requirement: Main is plugin-agnostic
`main.py` SHALL NOT contain any plugin-specific logic. It SHALL iterate over cards, load each plugin via the generic interface, and call `setup` and `render`.

#### Scenario: No plugin imports in main
- **WHEN** `main.py` is loaded
- **THEN** it does not import from any specific plugin module (e.g., `src.plugins.rss`)

#### Scenario: Plugin-agnostic card processing
- **WHEN** the server starts
- **THEN** `main.py` loops over cards, instantiates each plugin, and calls `setup`

### Requirement: Config validation is plugin-agnostic
Config validation SHALL delegate plugin-specific option validation to each plugin's `validate_options` method rather than hardcoding plugin-specific logic.

#### Scenario: Config validates plugin options via plugin class
- **WHEN** a card has a valid plugin name
- **THEN** config validation calls `plugin_class.validate_options(options, card_idx, filename)`

#### Scenario: Unknown plugin skips option validation
- **WHEN** a card has an unknown plugin name
- **THEN** config validation skips plugin-specific option validation
