## Purpose

RSS plugin for fetching and displaying feed items on the starter page.

## Requirements

### Requirement: Plugin abstract base class
The system SHALL provide an abstract `Plugin` base class in `src/plugin.py` with `setup`, `render`, `validate_options`, `parse_schedule`, and `load_template` methods.

#### Scenario: Plugin class has setup method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `setup(self, options, database, scheduler, logger)`

#### Scenario: Plugin class has render method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `render(self, options) → str` returning an HTML string

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
