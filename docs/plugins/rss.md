# RSS Plugin

Fetches and displays RSS feed items. Items are fetched on startup and refreshed on a cron schedule.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `feeds` | list of strings | yes | - | RSS feed URLs to fetch |
| `schedule` | string | yes | - | Cron expression for refresh schedule (e.g., `"0 */6 * * *"`) |
| `max_items` | integer | no | 10 | Maximum number of items to display |
| `images` | boolean | no | false | Fetch and cache feed images locally |

## Example

```yaml
cards:
  - title: News
    plugin: rss
    options:
      feeds:
        - https://example.com/feed.xml
        - https://other.com/rss
      schedule: "0 */6 * * *"
      max_items: 15
      images: true
```

Images are cached locally in `cache/rss/<card_id>/` and served as static files.
