## Requirements

### Requirement: Calendar plugin options
The system SHALL accept the following options for calendar cards:

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `calendars` | list | yes | - | List of calendar objects (see below) |
| `time_window_days` | integer | no | `7` | Number of days to look ahead for events |
| `max_events` | integer | no | `10` | Maximum number of events to display |
| `schedule` | string | yes | - | Cron expression for refresh schedule (e.g., `"*/30 * * * *"`) |

Each entry in `calendars` SHALL have:

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `url` | string | yes | - | Calendar URL (CalDAV server or ICS file URL) |
| `name` | string | yes | - | Display name for the calendar (e.g., `"Work"`, `"Personal"`) |
| `color` | string | no | - | Hex color code for visual indicator (e.g., `"#3b82f6"`) |
| `link_url` | string | no | - | URL to open when an event from this calendar is clicked |
| `type` | string | no | `"caldav"` | Calendar type: `"caldav"` or `"ics"` |
| `username` | string | no | - | Username for HTTP Basic authentication (CalDAV only) |
| `password` | string | no | - | Password for HTTP Basic authentication (CalDAV only) |
| `auth_type` | string | no | `"none"` | Authentication type: `"none"`, `"basic"`, or `"bearer"` |
| `bearer_token` | string | no | - | Bearer token for token-based authentication (required when `auth_type` is `"bearer"`) |

#### Scenario: Valid config with calendar name
- **WHEN** a card has `plugin: calendar` with `calendars` containing an entry with `url`, `name`, and `schedule`
- **THEN** config validation passes

#### Scenario: Valid config with calendar color
- **WHEN** a card has `plugin: calendar` with `calendars` containing an entry with `url`, `name`, and `color: "#3b82f6"`
- **THEN** config validation passes and events from this calendar display with the specified color

#### Scenario: Valid config with calendar link_url
- **WHEN** a card has `plugin: calendar` with `calendars` containing an entry with `url`, `name`, and `link_url: "https://example.com/cal"`
- **THEN** config validation passes

#### Scenario: Invalid calendar link_url type
- **WHEN** a calendar entry has `link_url` that is not a string
- **THEN** a configuration error is raised

#### Scenario: Missing name in calendar entry
- **WHEN** a calendar entry has `url` but no `name`
- **THEN** a configuration error is raised

#### Scenario: Invalid color type
- **WHEN** a calendar entry has `color` that is not a string
- **THEN** a configuration error is raised

#### Scenario: Valid config with single calendar
- **WHEN** a card has `plugin: calendar` with `calendars` containing one entry with `url`, `name`, and `schedule`
- **THEN** config validation passes

#### Scenario: Valid config with ICS calendar
- **WHEN** a card has `plugin: calendar` with `calendars` containing an entry with `type: ics`, `name`, and a public ICS URL
- **THEN** config validation passes and the plugin fetches the ICS file via HTTP

#### Scenario: Valid config with multiple calendars
- **WHEN** a card has `plugin: calendar` with `calendars` containing multiple entries, each with `url`, `name`, and type options
- **THEN** config validation passes

#### Scenario: Valid config with no auth on a calendar
- **WHEN** a calendar entry has `url`, `name`, but no auth options
- **THEN** config validation passes

#### Scenario: Missing calendars
- **WHEN** a calendar card has no `calendars` option
- **THEN** a configuration error is raised

#### Scenario: Empty calendars list
- **WHEN** a calendar card has `calendars: []`
- **THEN** a configuration error is raised

#### Scenario: Calendar entry missing url
- **WHEN** a calendar entry in `calendars` has no `url`
- **THEN** a configuration error is raised

#### Scenario: Invalid calendar type
- **WHEN** a calendar entry has `type` that is not `"caldav"` or `"ics"`
- **THEN** a configuration error is raised

#### Scenario: Missing schedule
- **WHEN** a calendar card has no `schedule` option
- **THEN** a configuration error is raised

#### Scenario: Invalid schedule format
- **WHEN** a calendar card has `schedule` that is not a valid cron expression (5 or 6 fields)
- **THEN** a configuration error is raised

#### Scenario: Invalid auth_type
- **WHEN** a calendar entry has `auth_type` that is not `"none"`, `"basic"`, or `"bearer"`
- **THEN** a configuration error is raised

#### Scenario: Bearer auth without token
- **WHEN** a calendar entry has `auth_type: bearer` but no `bearer_token`
- **THEN** a configuration error is raised

#### Scenario: Invalid time_window_days type
- **WHEN** a calendar card has `time_window_days` that is not a positive integer
- **THEN** a configuration error is raised

#### Scenario: Invalid max_events type
- **WHEN** a calendar card has `max_events` that is not a positive integer
- **THEN** a configuration error is raised

### Requirement: Calendar plugin fetches events from CalDAV servers
The system SHALL provide a `calendar` plugin that connects to one or more CalDAV servers, fetches upcoming events within a configurable time window, merges events from all calendars, and caches the result in the database.

#### Scenario: Successful CalDAV event fetch
- **WHEN** a calendar entry has `type: caldav` with valid auth options
- **THEN** the system connects to the CalDAV server and fetches events

#### Scenario: Successful ICS event fetch
- **WHEN** a calendar entry has `type: ics` with a valid ICS URL
- **THEN** the system fetches the ICS file via HTTP GET and parses events

#### Scenario: ICS fetch with no auth
- **WHEN** a calendar entry has `type: ics` and no auth options
- **THEN** the system fetches the ICS file without authentication

### Requirement: Calendar card displays upcoming events
The calendar card SHALL display a list of upcoming events with date, time, summary, and source calendar name, merged from all configured calendars.

#### Scenario: Events displayed with calendar name
- **WHEN** events are fetched from multiple calendars with `name` attributes
- **THEN** each event displays its source calendar name

#### Scenario: Events displayed with color indicator
- **WHEN** events are fetched from calendars with `color` attributes
- **THEN** each event displays a color indicator (dot or border) using the calendar's color

#### Scenario: Events without color
- **WHEN** an event is from a calendar without a `color` attribute
- **THEN** the event displays without a color indicator

#### Scenario: Events with calendar link_url are clickable
- **WHEN** events are fetched from a calendar with a `link_url` attribute
- **THEN** each event from that calendar is wrapped in an `<a>` tag with `href` set to the calendar's `link_url`, `target="_blank"`, and `rel="noopener"`

#### Scenario: Events without calendar link_url are not wrapped
- **WHEN** an event is from a calendar without a `link_url` attribute
- **THEN** the event is not wrapped in an `<a>` tag

#### Scenario: All-day events display date only
- **WHEN** an event is an all-day event
- **THEN** the event displays only the date (no "All day" text)

#### Scenario: Timed events display date and time
- **WHEN** an event has a specific time
- **THEN** the event displays both the date and time
