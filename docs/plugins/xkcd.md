# XKCD Plugin

Fetches and displays the latest XKCD comic. The comic is fetched on startup and refreshed on a cron schedule.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `schedule` | string | yes | - | Cron expression for refresh schedule (e.g., `"0 9 * * *"`) |

## Example

```yaml
cards:
  - title: XKCD
    plugin: xkcd
    options:
      schedule: "0 9 * * *"
```

## Features

- Displays the comic image, title, and alt text description
- Comic image links to the XKCD page
- Includes a link to the "Explain XKCD" page for that comic
- Comic image is cached locally (one image at a time)
- Only the most recent comic is kept in the database
