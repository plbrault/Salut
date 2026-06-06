# Template Variables

## Purpose

Server-side and client-side template variable resolution for dynamic content in config values and rendered HTML.

## Requirements

### Requirement: Server-side `${...}` variable resolution
The system SHALL recursively resolve `${...}` template variables in all string values of the loaded YAML config. Variables reference config keys using dot notation (e.g., `${user_info.short_name}`).

#### Scenario: Variable in card title
- **WHEN** a card has `title: "${user_info.short_name}'s Page"`
- **THEN** the rendered card title shows the resolved value (e.g., "Chris's Page")

#### Scenario: Variable in HTML card content
- **WHEN** an HTML card has `html: "<p>Hello ${user_info.short_name}</p>"`
- **THEN** the rendered HTML contains the resolved value

#### Scenario: Variable in card option
- **WHEN** a card option string contains `${user_info.long_name}`
- **THEN** the option value is resolved before being passed to the plugin

#### Scenario: Undefined variable preserved
- **WHEN** a string contains `${nonexistent.key}` and the key does not exist in the config
- **THEN** the placeholder is preserved as-is in the output

#### Scenario: Nested variable resolution
- **WHEN** a config value is `${user_info.short_name}` and `user_info.short_name` is `"Chris"`
- **THEN** the resolved value is `"Chris"`

### Requirement: Client-side `{{...}}` variable replacement
The system SHALL replace all `{{...}}` placeholders in the rendered page HTML using client-side JavaScript. Built-in variables include `{{time_emoji}}`, `{{date}}`, and `{{theme_toggle}}`.

#### Scenario: Time emoji replacement
- **WHEN** the page renders and contains `{{time_emoji}}`
- **THEN** the placeholder is replaced with the appropriate time-of-day emoji

#### Scenario: Date replacement
- **WHEN** the page renders and contains `{{date}}`
- **THEN** the placeholder is replaced with the localized current date

#### Scenario: Theme toggle replacement
- **WHEN** the page renders and contains `{{theme_toggle}}`
- **THEN** the placeholder is replaced with a theme toggle button

#### Scenario: Variable in card content
- **WHEN** an HTML card's rendered content contains `{{time_emoji}}`
- **THEN** the placeholder is replaced with the emoji

#### Scenario: Unknown variable preserved
- **WHEN** the page contains `{{unknown_var}}`
- **THEN** the placeholder is preserved as-is in the output
