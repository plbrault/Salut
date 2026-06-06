## MODIFIED Requirements

### Requirement: Config schema is validated
The system SHALL validate the parsed config has the required structure.

#### Scenario: Valid config structure
- **WHEN** the config has a `page_title` string, a `page_header` string, a `language` string, a `user_info` object with `short_name` and `long_name` strings, a `columns` integer, and a `cards` list with at least one card, each card having `title`, `plugin`, and `options`
- **THEN** the config is accepted

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
