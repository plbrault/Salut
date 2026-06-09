## Purpose

YAML configuration file loading with fallback pattern and schema validation.

## Requirements

### Requirement: YAML config is loaded on startup
The system SHALL load a YAML config file from the project root when the server starts, using a fallback pattern.

#### Scenario: User config exists
- **WHEN** the server starts and `config.yml` exists with valid YAML
- **THEN** the parsed config from `config.yml` is used

#### Scenario: User config missing, default config exists
- **WHEN** the server starts and `config.yml` does not exist but `starter.yml` exists with valid YAML
- **THEN** the parsed config from `starter.yml` is used

#### Scenario: Both config files missing
- **WHEN** the server starts and neither `config.yml` nor `starter.yml` exist
- **THEN** the server starts with a clear error message

#### Scenario: Config file has YAML syntax errors
- **WHEN** the server starts and the active config file contains invalid YAML
- **THEN** the server starts with a clear error message naming the parse error

### Requirement: Config schema is validated
The system SHALL validate the parsed config has the required structure.

#### Scenario: Valid config structure
- **WHEN** the config has a `page_title` string, a `page_header` string, a `language` string, a `user_info` object with `short_name` and `long_name` strings, a `columns` integer, and a `cards` list with at least one card, each card having `title`, `plugin`, and `options`
- **THEN** the config is accepted

#### Scenario: Optional admin_password
- **WHEN** the config has an `admin_password` field with a non-empty string value
- **THEN** the config is accepted and the admin panel is enabled

#### Scenario: Missing columns
- **WHEN** the config has no `columns` field
- **THEN** a validation error is raised indicating columns are required

#### Scenario: Invalid columns type
- **WHEN** the config has a `columns` field that is not an integer
- **THEN** a validation error is raised indicating columns must be an integer

#### Scenario: Missing cards
- **WHEN** the config has no `cards` field
- **THEN** a validation error is raised indicating cards are required

#### Scenario: Empty cards
- **WHEN** the config has a `cards` field that is an empty list
- **THEN** a validation error is raised indicating cards must be a non-empty list

#### Scenario: Missing card title
- **WHEN** a card has no `title` field
- **THEN** a validation error is raised indicating the title is required

#### Scenario: Missing card plugin
- **WHEN** a card has no `plugin` field
- **THEN** a validation error is raised indicating the plugin is required

#### Scenario: Card with valid column
- **WHEN** a card has `column: 2` and the config has `columns: 3`
- **THEN** the config is accepted

#### Scenario: Card with column exceeding total columns
- **WHEN** a card has `column: 4` and the config has `columns: 3`
- **THEN** a validation error is raised indicating column exceeds total columns

#### Scenario: Card with column and colspan exceeding total columns
- **WHEN** a card has `column: 2`, `colspan: 3`, and the config has `columns: 4`
- **THEN** a validation error is raised indicating column + colspan exceeds total columns

#### Scenario: Invalid column type
- **WHEN** a card has `column` that is not an integer
- **THEN** a validation error is raised indicating column must be an integer

#### Scenario: Invalid column value
- **WHEN** a card has `column: 0`
- **THEN** a validation error is raised indicating column must be a positive integer

### Requirement: Page title is required
The system SHALL require a `page_title` string field in the config.

#### Scenario: Missing page title
- **WHEN** the config has no `page_title` field
- **THEN** a validation error is raised indicating page_title is required

#### Scenario: Invalid page title type
- **WHEN** the config has a `page_title` field that is not a string
- **THEN** a validation error is raised indicating page_title must be a string

### Requirement: Page header is required
The system SHALL require a `page_header` string field in the config.

#### Scenario: Missing page header
- **WHEN** the config has no `page_header` field
- **THEN** a validation error is raised indicating page_header is required

#### Scenario: Invalid page header type
- **WHEN** the config has a `page_header` field that is not a string
- **THEN** a validation error is raised indicating page_header must be a string

### Requirement: Language is required
The system SHALL require a `language` string field in the config.

#### Scenario: Missing language
- **WHEN** the config has no `language` field
- **THEN** a validation error is raised indicating language is required

#### Scenario: Invalid language type
- **WHEN** the config has a `language` field that is not a string
- **THEN** a validation error is raised indicating language must be a string

#### Scenario: Invalid language code
- **WHEN** the config has a `language` field that is not a valid BCP 47 tag or supported simple code
- **THEN** a validation error is raised indicating language is invalid

#### Scenario: Simple language code is normalized
- **WHEN** the config has a `language` field with a simple code (e.g., `en`, `fr`)
- **THEN** the language is normalized to its BCP 47 default (e.g., `en-US`, `fr-FR`)

### Requirement: User info is required
The system SHALL require a `user_info` object with `short_name` and `long_name` string fields.

#### Scenario: Missing user info
- **WHEN** the config has no `user_info` field
- **THEN** a validation error is raised indicating user_info is required

#### Scenario: Missing short name
- **WHEN** the config has a `user_info` field but no `short_name` field
- **THEN** a validation error is raised indicating user_info.short_name is required

#### Scenario: Missing long name
- **WHEN** the config has a `user_info` field but no `long_name` field
- **THEN** a validation error is raised indicating user_info.long_name is required

#### Scenario: Invalid short name type
- **WHEN** the config has a `user_info.short_name` field that is not a string
- **THEN** a validation error is raised indicating user_info.short_name must be a string

#### Scenario: Invalid long name type
- **WHEN** the config has a `user_info.long_name` field that is not a string
- **THEN** a validation error is raised indicating user_info.long_name must be a string

### Requirement: Config variable resolution
The system SHALL resolve `${...}` template variables in config values from three sources: config values, secrets, and i18n translations.

#### Scenario: Config variable resolved
- **WHEN** a config value contains `${page_title}` and the config has `page_title: "My Page"`
- **THEN** the variable is resolved to `"My Page"`

#### Scenario: Secret variable resolved
- **WHEN** a config value contains `${secrets.api_key}` and `secrets.yml` has `api_key: "abc123"`
- **THEN** the variable is resolved to `"abc123"`

#### Scenario: i18n variable resolved
- **WHEN** a config value contains `${i18n.hi}` and the global translations contain `"hi": "Salut"`
- **THEN** the variable is resolved to `"Salut"`

#### Scenario: i18n variable with missing key
- **WHEN** a config value contains `${i18n.unknown}` and no translation exists for that key
- **THEN** the variable is resolved to the key name `"unknown"`

### Requirement: Favicon is optional
The system SHALL accept an optional `favicon` string field in the config.

#### Scenario: Favicon provided
- **WHEN** the config has `favicon: "👋"`
- **THEN** the favicon value is passed to the template context as a string

#### Scenario: Favicon omitted
- **WHEN** the config has no `favicon` field
- **THEN** no favicon value is passed to the template context

#### Scenario: Invalid favicon type
- **WHEN** the config has a `favicon` field that is not a string
- **THEN** a validation error is raised indicating favicon must be a string
