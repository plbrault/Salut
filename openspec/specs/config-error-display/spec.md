### Requirement: Application displays error page for invalid config
The application SHALL start even when the configuration file contains invalid YAML or fails validation. It SHALL display a user-friendly error page with the specific error message instead of crashing.

#### Scenario: Invalid YAML syntax
- **WHEN** `config.yml` contains invalid YAML syntax (e.g., unclosed quotes, bad indentation)
- **THEN** the application starts and the web page displays an error message indicating the YAML parse error with details

#### Scenario: Config validation failure
- **WHEN** `config.yml` is valid YAML but fails semantic validation (e.g., missing required fields, wrong types)
- **THEN** the application starts and the web page displays an error message indicating the validation error with details

#### Scenario: No config file found
- **WHEN** neither `config.yml` nor `starter.yml` exists
- **THEN** the application starts and the web page displays an error message indicating no config file was found

#### Scenario: Empty config file
- **WHEN** `config.yml` exists but is empty
- **THEN** the application starts and the web page displays an error message indicating the config file is empty

#### Scenario: Valid config
- **WHEN** `config.yml` is valid and passes all validation
- **THEN** the application renders the start page normally with no error displayed
