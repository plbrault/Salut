## Purpose

A basic admin panel at `/admin` for managing the Salut start page configuration, restarting the server, and pulling updates.

## Requirements

### Requirement: Admin panel requires admin_password
The admin panel SHALL only be accessible when `admin_password` is set to a non-empty string in the config.

#### Scenario: No admin_password in config
- **WHEN** the config has no `admin_password` field
- **THEN** accessing `/admin` returns a 403 page instructing the user to set `admin_password` in their config and restart the server

#### Scenario: admin_password is empty string
- **WHEN** the config has `admin_password: ""` (resolved to empty from secrets.yml)
- **THEN** accessing `/admin` returns a 403 page instructing the user to set a value for `admin_password` in `secrets.yml` and restart the server

#### Scenario: admin_password is set
- **WHEN** the config has a non-empty `admin_password` value
- **THEN** accessing `/admin` shows the login page

### Requirement: Admin login with session cookie
The admin panel SHALL authenticate users via password and maintain session via HMAC-signed cookie.

#### Scenario: Successful login
- **WHEN** the user submits the correct password as JSON to `POST /admin/login`
- **THEN** the server sets a signed session cookie and redirects to `/admin`

#### Scenario: Failed login
- **WHEN** the user submits an incorrect password
- **THEN** the login page is re-rendered with an "Invalid password" error

#### Scenario: Login form sends JSON
- **WHEN** the login form is submitted
- **THEN** the request body is JSON with a `password` field (not form-encoded)

#### Scenario: Session cookie expiry
- **WHEN** a session cookie is set
- **THEN** it expires after 7 days

#### Scenario: Logout
- **WHEN** the user submits `POST /admin/logout`
- **THEN** the session cookie is deleted and the user is redirected to `/admin/login`

#### Scenario: Already authenticated on login page
- **WHEN** an authenticated user visits `/admin/login`
- **THEN** they are redirected to `/admin`

### Requirement: Admin page displays config editor
The admin page SHALL display a config editor with CodeMirror YAML syntax highlighting when `config.yml` exists.

#### Scenario: config.yml exists
- **WHEN** `config.yml` exists
- **THEN** the admin page shows a CodeMirror editor pre-filled with the config content, along with Load Config, Validate, and Save & Reload buttons

#### Scenario: config.yml does not exist
- **WHEN** `config.yml` does not exist
- **THEN** the admin page shows a message suggesting the user create one based on `starter.yml`, and hides the editor-dependent buttons

### Requirement: Config validation
The admin panel SHALL validate YAML config before saving.

#### Scenario: Valid YAML and valid config
- **WHEN** the user clicks Validate with valid YAML that passes schema validation
- **THEN** a green "Config is valid" message is displayed

#### Scenario: Invalid YAML syntax
- **WHEN** the user clicks Validate with YAML that has syntax errors
- **THEN** a red error message with the YAML parse error is displayed

#### Scenario: Valid YAML but invalid config
- **WHEN** the user clicks Validate with valid YAML that fails schema validation
- **THEN** a red error message with the validation error is displayed

### Requirement: Config save and reload
The admin panel SHALL save the config to `config.yml` and reload the app state without restarting the server.

#### Scenario: Save valid config
- **WHEN** the user clicks Save & Reload with valid config content
- **THEN** the config is written to `config.yml` and the app state is reloaded (scheduler jobs, etc.)

#### Scenario: Save invalid config
- **WHEN** the user clicks Save & Reload with invalid config
- **THEN** the save is rejected and the error is shown (config file is not modified)

### Requirement: Reload config
The admin panel SHALL provide a button to reload the config without saving.

#### Scenario: Reload config
- **WHEN** the user clicks Reload Config
- **THEN** the app state is reloaded from the current config file (scheduler jobs are reinitialized)

### Requirement: Server restart
The admin panel SHALL provide a button to restart the server.

#### Scenario: Restart on non-systemd
- **WHEN** the user clicks Restart and `INVOCATION_ID` is not set
- **THEN** the server replaces itself via `os.execv`

#### Scenario: Restart on systemd
- **WHEN** the user clicks Restart and `INVOCATION_ID` is set (systemd service)
- **THEN** `systemctl --user restart salut` is executed

#### Scenario: Restart shows modal
- **WHEN** the user clicks Restart
- **THEN** a modal is displayed saying the page will be unavailable until the server restarts, with an OK button that redirects to `/`

### Requirement: Server update
The admin panel SHALL provide a two-step update flow: first check for updates, then update if available.

#### Scenario: Check for updates when already up-to-date
- **WHEN** the user clicks "Check for updates" and the remote has no new commits
- **THEN** a message "No updates available" is displayed

#### Scenario: Check for updates when updates exist
- **WHEN** the user clicks "Check for updates" and the remote has new commits
- **THEN** a message "Update available: <commit-hash> <commit-message>" is displayed and the button changes to "Update & Restart"

#### Scenario: Check for updates with uncommitted changes
- **WHEN** the user clicks "Check for updates" and there are uncommitted git changes
- **THEN** an error message is displayed: "Uncommitted changes. Please commit or stash before updating."

#### Scenario: Check for updates fails
- **WHEN** the user clicks "Check for updates" and the git fetch fails (network error, etc.)
- **THEN** an error message with the failure details is displayed

#### Scenario: Update with uncommitted changes
- **WHEN** the user clicks "Update & Restart" and there are uncommitted git changes
- **THEN** an error message is displayed: "Uncommitted changes. Please commit or stash before updating."

#### Scenario: Update with git pull failure
- **WHEN** the user clicks "Update & Restart" and `git pull` fails
- **THEN** an error message with the git error is displayed

#### Scenario: Successful update
- **WHEN** the user clicks "Update & Restart" and git pull succeeds
- **THEN** dependencies are installed via `pipenv install`, the server restarts, and a modal is displayed

#### Scenario: Update on any branch
- **WHEN** the user clicks "Update & Restart"
- **THEN** the update pulls from the current branch's remote (regardless of which branch)

### Requirement: Log viewer
The admin panel SHALL provide a log viewer showing recent server log entries.

#### Scenario: Fetch logs
- **WHEN** the user clicks Fetch Logs
- **THEN** the last 500 log entries are displayed in reverse chronological order

#### Scenario: Log entry format
- **WHEN** log entries are displayed
- **THEN** each entry shows a timestamp, log level, and message

### Requirement: Server socket uses SO_REUSEADDR
The server SHALL create its listening socket with `SO_REUSEADDR` so that server restarts via `os.execv` can immediately rebind to the same port.

#### Scenario: Restart reuses port
- **WHEN** the server restarts via `os.execv`
- **THEN** the new process binds to the same port without "Address already in use" errors

### Requirement: Button loading states
The admin panel SHALL show a loading spinner and disable action buttons while a request is in flight.

#### Scenario: Button shows spinner during request
- **WHEN** the user clicks Load Config, Save & Reload, Reload Config, or Validate
- **THEN** a spinner appears inside the button and the button becomes disabled until the request completes

#### Scenario: Button re-enables after request
- **WHEN** a button request completes (success or error)
- **THEN** the spinner disappears and the button becomes enabled again

### Requirement: Config save and reload feedback
The admin panel SHALL display human-readable feedback when saving and reloading config.

#### Scenario: Save successful
- **WHEN** the user clicks Save & Reload with valid config content
- **THEN** a green message "Config saved and reloaded successfully" is displayed

#### Scenario: Save fails with YAML error
- **WHEN** the user clicks Save & Reload with invalid YAML syntax
- **THEN** a red error message with the YAML parse error is displayed

#### Scenario: Save fails with config error
- **WHEN** the user clicks Save & Reload with valid YAML that fails schema validation
- **THEN** a red error message with the validation error is displayed

#### Scenario: Old feedback clears on new action
- **WHEN** the user clicks Load Config, Save & Reload, Validate, or Reload Config
- **THEN** any previous feedback message is replaced with the new result

### Requirement: Load config feedback
The admin panel SHALL display human-readable feedback when loading config into the editor.

#### Scenario: Load successful
- **WHEN** the user clicks Load Config and the config is loaded into the editor
- **THEN** a green message "Config loaded successfully" is displayed

#### Scenario: Load fails
- **WHEN** the user clicks Load Config and an error occurs
- **THEN** a red error message with the error details is displayed

### Requirement: Reload config feedback
The admin panel SHALL display human-readable feedback when reloading config.

#### Scenario: Reload successful
- **WHEN** the user clicks Reload Config and the reload succeeds
- **THEN** a green message "Config reloaded successfully" is displayed

#### Scenario: Reload fails
- **WHEN** the user clicks Reload Config and an error occurs
- **THEN** a red error message with the error details is displayed
