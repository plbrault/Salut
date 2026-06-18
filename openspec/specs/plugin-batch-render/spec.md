## Purpose

Batch rendering interface for plugins, allowing multiple cards of the same plugin type to be rendered in a single call.

## Requirements

### Requirement: Plugin batch render interface
The system SHALL call each plugin's `render` method once per plugin type, passing a list of all cards using that plugin. Each card in the list SHALL be represented as a dict with `options` (the plugin-specific configuration) and `card_id` (the unique identifier for the card). The plugin SHALL return a list of HTML strings in the same order as the input list.

#### Scenario: Plugin receives multiple cards
- **WHEN** three cards use the `rss` plugin
- **THEN** the `rss` plugin's `render` method is called once with a list of three card dicts

#### Scenario: Plugin returns HTML for each card
- **WHEN** a plugin's `render` method receives a list of N cards
- **THEN** the method returns a list of exactly N HTML strings

#### Scenario: Output order matches input order
- **WHEN** a plugin receives cards in order [A, B, C]
- **THEN** the returned HTML strings correspond to [A's HTML, B's HTML, C's HTML]

#### Scenario: Single card plugin
- **WHEN** only one card uses a particular plugin
- **THEN** the plugin's `render` method receives a list with one card dict and returns a list with one HTML string

### Requirement: Orchestrator batches cards by plugin type
The system SHALL group cards by their `plugin` field before rendering. For each plugin type, the system SHALL call the plugin's `render` method once with all cards of that type, then distribute the returned HTML strings back to their respective card positions.

#### Scenario: Cards grouped by plugin type
- **WHEN** the page has cards using plugins [weather, rss, weather, search, rss]
- **THEN** the `weather` plugin receives 2 cards, `rss` receives 2 cards, and `search` receives 1 card

#### Scenario: Rendering preserves card order
- **WHEN** the original card list is [weather-1, rss-1, weather-2, search-1, rss-2]
- **THEN** the rendered output maintains the same card ordering on the page

#### Scenario: Plugin error affects all cards of that type
- **WHEN** a plugin's batch render raises an exception
- **THEN** all cards using that plugin display an error message

### Requirement: Batch render data optimization
Plugins MAY use the batch render call to optimize data fetching across multiple cards. For example, a plugin may query the database once for all cards' data instead of once per card.

#### Scenario: Batch data fetching
- **WHEN** a plugin receives multiple cards with different card IDs
- **THEN** the plugin MAY query the database once to fetch data for all cards

#### Scenario: Individual card processing
- **WHEN** a plugin receives multiple cards
- **THEN** the plugin SHALL still produce independent HTML output for each card
