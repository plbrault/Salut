# Search Plugin

## Purpose

This capability provides a search bar card that allows users to search the web directly from their starter page. The plugin renders a configurable search form that submits to DuckDuckGo.

## Requirements

### Requirement: Search bar rendering
The system SHALL render a search bar with a configurable button text.

#### Scenario: Custom button text
- **WHEN** a search card has `button_text` option set to "Go"
- **THEN** the search button displays "Go"

#### Scenario: Default button text
- **WHEN** a search card has no `button_text` option
- **THEN** the search button displays "Search"

### Requirement: Search provider support
The system SHALL support DuckDuckGo and Wikipedia as search providers.

#### Scenario: DuckDuckGo search
- **WHEN** a search card has `provider` option set to "duckduckgo"
- **THEN** the search form submits to DuckDuckGo's search endpoint

#### Scenario: Wikipedia search
- **WHEN** a search card has `provider` option set to "wikipedia"
- **THEN** the search form submits to Wikipedia's search endpoint

#### Scenario: Wikipedia search with language
- **WHEN** a search card has `provider` set to "wikipedia" and `language` set to "fr"
- **THEN** the search form submits to French Wikipedia

#### Scenario: Wikipedia default language
- **WHEN** a search card has `provider` set to "wikipedia" with no `language` option
- **THEN** the search form submits to English Wikipedia

#### Scenario: Missing provider
- **WHEN** a search card has no `provider` option
- **THEN** the system raises a configuration error

#### Scenario: Unsupported provider
- **WHEN** a search card has a `provider` option that is not "duckduckgo" or "wikipedia"
- **THEN** the system raises a configuration error

### Requirement: Search form functionality
The system SHALL provide a functional search form with configurable target.

#### Scenario: Form submission
- **WHEN** user types a query and presses Enter or clicks search
- **THEN** the browser navigates to DuckDuckGo search results for that query

#### Scenario: Empty query
- **WHEN** user submits the form with an empty query
- **THEN** the form does not submit

#### Scenario: Open results in new tab
- **WHEN** a search card has `results_in_new_tab` option set to true
- **THEN** the search results open in a new browser tab

#### Scenario: Default results target
- **WHEN** a search card has no `results_in_new_tab` option
- **THEN** the search results open in the same tab
