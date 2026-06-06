## ADDED Requirements

### Requirement: Plugin abstract base class
The system SHALL provide an abstract `Plugin` base class in `src/plugins/base.py` with `setup` and `render` methods.

#### Scenario: Plugin class has setup method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `setup(self, options, database, scheduler, logger)`

#### Scenario: Plugin class has render method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `render(self, options) → str` returning an HTML string

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

### Requirement: Main is plugin-agnostic
`main.py` SHALL NOT contain any plugin-specific logic. It SHALL iterate over cards, load each plugin via the generic interface, and call `setup` and `render`.

#### Scenario: No plugin imports in main
- **WHEN** `main.py` is loaded
- **THEN** it does not import from any specific plugin module (e.g., `src.plugins.rss`)

#### Scenario: Plugin-agnostic card processing
- **WHEN** the server starts
- **THEN** `main.py` loops over cards, instantiates each plugin, and calls `setup`
