# GitHub Notifications Plugin

## Purpose

Displays unread GitHub notifications in a card using the GitHub Notifications API with Personal Access Token authentication.

## Requirements

### Requirement: GitHub notifications plugin displays unread notifications
The system SHALL display unread GitHub notifications in a card, fetched via the GitHub Notifications API.

#### Scenario: Notifications displayed
- **WHEN** a card has `plugin: github-notifications` with a valid token
- **THEN** unread GitHub notifications are displayed in the card

### Requirement: Authentication via token
The system SHALL authenticate to the GitHub API using a Personal Access Token provided via the `token` option. The token SHOULD be stored in `secrets.yml` and referenced as `${secrets.github_token}`.

#### Scenario: Valid token
- **WHEN** a valid GitHub token is provided
- **THEN** the plugin fetches notifications successfully

#### Scenario: Missing token
- **WHEN** `token` is not provided or empty
- **THEN** the card renders an error message instructing the user to configure a GitHub token

#### Scenario: Invalid token
- **WHEN** the GitHub API returns 401 Unauthorized
- **THEN** a warning is logged and the card shows an error message

### Requirement: Notifications fetched from GitHub API
The system SHALL fetch notifications from `GET https://api.github.com/notifications` using the `Authorization: Bearer <token>` header. Only unread notifications SHALL be fetched (default API behavior).

#### Scenario: Successful fetch
- **WHEN** the GitHub API returns notifications
- **THEN** the notifications are parsed and stored in the database

#### Scenario: API error
- **WHEN** the GitHub API returns an error
- **THEN** a warning is logged and the card shows no notifications

#### Scenario: Notification with missing fields
- **WHEN** a notification has null or missing values for `subject.url`, `reason`, `subject.title`, or `repository.full_name`
- **THEN** the notification is still stored and displayed, with missing fields defaulting to empty strings

### Requirement: Notifications grouped by thread
The system SHALL display each notification thread as a separate item. Each thread is identified by its `thread_id`.

#### Scenario: Multiple notifications from same repo
- **WHEN** there are multiple notifications from the same repository
- **THEN** each notification is displayed as a separate item

### Requirement: Notification display format
The system SHALL display each notification with: repository name, subject title, reason (lowercased, underscores replaced with spaces), and relative time. If any of these fields is missing or empty, it SHALL be displayed as an empty string.

#### Scenario: Notification item display
- **WHEN** a notification is rendered
- **THEN** the card shows the repo name, subject title, reason, and time since update

### Requirement: Clickable notifications
The system SHALL make each notification clickable, opening the notification URL in a new browser tab. The URL SHALL be derived from the `subject.url` API field by replacing `api.github.com/repos` with `github.com`.

#### Scenario: Click opens in new tab
- **WHEN** a user clicks a notification
- **THEN** the notification opens in a new browser tab

### Requirement: Optional schedule
The system SHALL accept an optional `schedule` option (cron expression). If absent, the default schedule is `*/5 * * * *` (every 5 minutes).

#### Scenario: Default schedule
- **WHEN** `schedule` is not provided
- **THEN** notifications are fetched every 5 minutes

#### Scenario: Custom schedule
- **WHEN** `schedule` is a valid cron expression
- **THEN** notifications are fetched on that schedule

### Requirement: Optional max_items
The system SHALL accept an optional `max_items` option (default: 10). Only the most recent notifications up to `max_items` SHALL be displayed.

#### Scenario: Default max_items
- **WHEN** `max_items` is not provided
- **THEN** at most 10 notifications are displayed

#### Scenario: Custom max_items
- **WHEN** `max_items` is set to 20
- **THEN** at most 20 notifications are displayed

### Requirement: Config validation
The system SHALL validate that `token` is provided and non-empty. If `schedule` is provided, it MUST be a valid cron expression. If `max_items` is provided, it MUST be a positive integer.

#### Scenario: Missing token
- **WHEN** `token` is not provided
- **THEN** a ConfigError is raised

#### Scenario: Empty token
- **WHEN** `token` is an empty string
- **THEN** a ConfigError is raised

#### Scenario: Invalid schedule
- **WHEN** `schedule` is provided but not a valid cron expression
- **THEN** a ConfigError is raised

#### Scenario: Invalid max_items
- **WHEN** `max_items` is provided but not a positive integer
- **THEN** a ConfigError is raised
