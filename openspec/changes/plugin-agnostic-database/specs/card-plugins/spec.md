## MODIFIED Requirements

### Requirement: Plugins render card content
The system SHALL load plugins from `src/plugins/` and use them to render card content.

#### Scenario: Plugin is loaded and executed
- **WHEN** a card specifies `plugin: html` with `options`
- **THEN** the system loads the corresponding plugin and calls its `render(options)` function

#### Scenario: Plugin returns rendered HTML
- **WHEN** a plugin's `render(options)` function is called
- **THEN** the function returns an HTML string

#### Scenario: Plugin error handling
- **WHEN** a plugin fails to load or raises an exception
- **THEN** the system displays an error message in the card instead of crashing

#### Scenario: Plugin setup_database is called at startup
- **WHEN** the server starts
- **THEN** the system calls `plugin_class.setup_database(database)` for each plugin before calling `setup`
