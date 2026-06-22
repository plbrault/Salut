# RSS Plugin

Fetches and displays RSS feed items. Items are fetched on startup and refreshed according to each card's cron schedule. Refresh checks run every 5 minutes, so a card's schedule is evaluated at the next 5-minute boundary after it becomes due.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `feeds` | list of strings | yes | - | RSS feed URLs to fetch. Order determines precedence for deduplication: when two feeds publish items with the same title, the one listed first is kept. |
| `schedule` | string | yes | - | Cron expression for refresh schedule (e.g., `"0 */6 * * *"`). Schedule granularity is 5 minutes — cards are checked every 5 minutes and refreshed if their schedule says they're due. |
| `max_items` | integer | no | 10 | Maximum number of items to display |
| `images` | boolean | no | false | Fetch and cache feed images locally |
| `include_fields` | list of strings | no | `["title"]` | Which RSS fields to extract. Valid values: `title`, `description`, `author`. `link` and `published` are always extracted. Feeds without titles automatically include `description`. |
| `truncate_fields` | dict | no | - | Max character lengths for fields. Keys: `title`, `description`, `author`, `feed_title`. Values can be integers or objects with `max_length` (integer) and optional `suffix` (string, default `"..."`). Truncation is word-boundary aware and applied at render time. |
| `distinct_from` | list of strings | no | - | List of card IDs to exclude items from. Items that appear in any of the referenced cards (matched by link URL or title) will be filtered out before `max_items` is applied. When both a dependency and its dependent refresh in the same cycle, the dependency is refreshed first. Dependencies are not refreshed more often than their own schedule. Circular dependencies are rejected at validation time. |

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
      include_fields:
        - title
        - description
      truncate_fields:
        title: 100
        description: { max_length: 200, suffix: "…" }
        feed_title: 30

  - title: Other News
    plugin: rss
    options:
      feeds:
        - https://example.com/feed.xml
        - https://different.com/rss
      schedule: "0 */6 * * *"
      distinct_from:
        - "news-card-id"
```

Images are cached locally in `cache/rss/<card_id>/` and served as static files.
