## MODIFIED Requirements

### Requirement: Plugin abstract base class
The system SHALL provide an abstract `Plugin` base class in `src/plugin.py` with `setup`, `render`, `setup_database`, `validate_options`, `parse_schedule`, and `load_template` methods.

#### Scenario: Plugin class has setup method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `setup(self, options, database, scheduler, logger)`

#### Scenario: Plugin class has render method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `render(self, options) → str` returning an HTML string

#### Scenario: Plugin class has setup_database method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `setup_database(database)` as a static method to create plugin-specific tables

#### Scenario: Plugin class has validate_options method
- **WHEN** a plugin class extends `Plugin`
- **THEN** it implements `validate_options(options, card_idx, filename)` as a static method to validate plugin-specific options

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
