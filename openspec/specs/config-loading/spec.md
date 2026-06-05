## Purpose

YAML configuration file loading with fallback pattern and schema validation.

## Requirements

### Requirement: YAML config is loaded on startup
The system SHALL load a YAML config file from the project root when the server starts, using a fallback pattern.

#### Scenario: User config exists
- **WHEN** the server starts and `config.yml` exists with valid YAML
- **THEN** the parsed config from `config.yml` is used

#### Scenario: User config missing, default config exists
- **WHEN** the server starts and `config.yml` does not exist but `starter.yaml` exists with valid YAML
- **THEN** the parsed config from `starter.yaml` is used

#### Scenario: Both config files missing
- **WHEN** the server starts and neither `config.yml` nor `starter.yaml` exist
- **THEN** the server starts with a clear error message

#### Scenario: Config file has YAML syntax errors
- **WHEN** the server starts and the active config file contains invalid YAML
- **THEN** the server starts with a clear error message naming the parse error

### Requirement: Config schema is validated
The system SHALL validate the parsed config has the required structure.

#### Scenario: Valid config structure
- **WHEN** the config has a `columns` array with at least one column containing a `cards` array with at least one card, each card having `title` and `type`
- **THEN** the config is accepted

#### Scenario: Missing columns
- **WHEN** the config has no `columns` field
- **THEN** a validation error is raised indicating columns are required

#### Scenario: Missing card title
- **WHEN** a card has no `title` field
- **THEN** a validation error is raised indicating the title is required

#### Scenario: Missing card type
- **WHEN** a card has no `type` field
- **THEN** a validation error is raised indicating the type is required
