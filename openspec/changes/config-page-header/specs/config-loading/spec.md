## MODIFIED Requirements

### Requirement: Config schema is validated
The system SHALL validate the parsed config has the required structure.

#### Scenario: Valid config structure
- **WHEN** the config has a `page_title` string, a `page_header` string, a `user_info` object with `short_name` and `long_name` strings, and a `columns` array with at least one column containing a `cards` array with at least one card, each card having `title` and `type`
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

## ADDED Requirements

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
