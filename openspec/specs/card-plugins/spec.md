## Purpose

Plugin-based card rendering system for the starter page. Cards use plugins to render their content, with support for the `html` plugin and colspan.

## Requirements

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

#### Scenario: Plugin init_schema is called at startup
- **WHEN** the server starts
- **THEN** the system calls `plugin_class.init_schema(database)` for each plugin before calling `setup`

### Requirement: HTML plugin renders arbitrary HTML
The system SHALL provide an `html` plugin that renders HTML from the card's `options.html` field.

#### Scenario: HTML plugin renders content
- **WHEN** a card has `plugin: html` and `options: { html: "<p>Hello</p>" }`
- **THEN** the rendered card contains the HTML content

#### Scenario: HTML plugin with no html option
- **WHEN** a card has `plugin: html` but no `options.html` field
- **THEN** the card renders empty content

### Requirement: Cards support colspan
The system SHALL support a `colspan` field on cards to span multiple columns.

#### Scenario: Card spans multiple columns
- **WHEN** a card has `colspan: 2`
- **THEN** the card occupies the width of 2 columns

#### Scenario: Default colspan
- **WHEN** a card has no `colspan` field
- **THEN** the card occupies 1 column (default)

### Requirement: Card config schema
The system SHALL accept a flat `cards` list at the top level, with each card having `title`, `plugin`, `options`, and optional `colspan` fields.

#### Scenario: Valid card config
- **WHEN** a card has `title` (string), `plugin` (string), and `options` (dict)
- **THEN** the config is accepted

#### Scenario: Card with colspan
- **WHEN** a card has `colspan` (integer)
- **THEN** the card spans the specified number of columns

#### Scenario: Card without colspan
- **WHEN** a card has no `colspan` field
- **THEN** the card spans 1 column (default)

#### Scenario: Missing card title
- **WHEN** a card has no `title` field
- **THEN** a validation error is raised

#### Scenario: Missing card plugin
- **WHEN** a card has no `plugin` field
- **THEN** a validation error is raised
