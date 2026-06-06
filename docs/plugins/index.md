# Plugins

Plugins render card content. Each plugin lives in `src/plugins/<name>/` and exposes a `render(options)` function.

## Available Plugins

### html

Renders arbitrary HTML from the card's `options.html` field.

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `html` | string | HTML content to render |

**Example:**

```yaml
cards:
  - title: My Card
    plugin: html
    options:
      html: "<p>Hello world!</p>"
```

If no `html` option is provided, the card renders empty content.

### rss

Fetches and displays RSS feed items. Items are fetched on startup and refreshed on a cron schedule.

**Options:**

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `feeds` | list of strings | yes | - | RSS feed URLs to fetch |
| `schedule` | string | yes | - | Cron expression for refresh schedule (e.g., `"0 */6 * * *"`)|
| `max_items` | integer | no | 10 | Maximum number of items to display |
| `images` | boolean | no | false | Fetch and cache feed images locally |

**Example:**

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

## Writing a Plugin

Create a directory under `src/plugins/` with an `__init__.py`:

```python
# src/plugins/myplugin/__init__.py

def render(options):
    # Return an HTML string
    return "<p>Hello from my plugin!</p>"
```

The plugin will be automatically discovered and can be used with `plugin: myplugin` in your config.
