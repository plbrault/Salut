# Calendar Plugin

Fetches and displays upcoming calendar events from CalDAV or ICS feeds. Events are fetched on startup and refreshed on a cron schedule.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `calendars` | list | yes | - | List of calendar entries (see below) |
| `schedule` | string | yes | - | Cron expression for refresh schedule (e.g., `"0 */1 * * *"`) |
| `time_window_days` | integer | no | 7 | Number of days ahead to fetch events |
| `max_events` | integer | no | 10 | Maximum number of events to display |

### Calendar Entry

Each item in `calendars` is an object with:

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `url` | string | yes | - | Calendar URL (CalDAV or ICS) |
| `name` | string | yes | - | Display name for the calendar |
| `type` | string | no | `"caldav"` | Calendar type: `"caldav"` or `"ics"` |
| `color` | string | no | - | Hex color for the calendar (e.g., `"#3b82f6"`) |
| `link_url` | string | no | - | URL to open when an event from this calendar is clicked |
| `auth_type` | string | no | `"none"` | Authentication: `"none"`, `"basic"`, or `"bearer"` |
| `username` | string | no | - | Username for basic auth |
| `password` | string | no | - | Password for basic auth (use `${secrets...}` syntax) |
| `bearer_token` | string | no | - | Bearer token for auth (required when `auth_type: bearer`) |

## Example

```yaml
cards:
  - title: Calendar
    plugin: calendar
    options:
      calendars:
        - url: https://caldav.example.com/user/cal1/
          name: Personal
          type: caldav
          color: "#3b82f6"
          auth_type: basic
          username: user
          password: ${secrets.calendar_password}
        - url: https://example.com/holidays.ics
          name: Holidays
          type: ics
          link_url: https://example.com/holidays
      schedule: "0 */1 * * *"
      time_window_days: 14
      max_events: 15
```

Events are cached in the `calendar_events` table and refreshed according to the schedule.
