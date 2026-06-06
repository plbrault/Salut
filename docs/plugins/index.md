# Plugins

Plugins render card content. Each plugin lives in `src/plugins/<name>/` and extends the abstract `Plugin` class in `src/plugin.py`.

## Plugin Architecture

Each plugin is a class that extends `Plugin` with these methods:

- `setup(options, database, scheduler, logger)` — Initialize the plugin for a card. Called once at startup.
- `render(options)` — Return HTML string for the card.
- `validate_options(options, card_idx, filename)` — Validate plugin-specific options. Raise `ConfigError` if invalid.
- `setup_database(database)` — Initialize database tables for this plugin. Called once at startup.

Plugins are automatically discovered by scanning `src/plugins/<name>/` for classes that extend `Plugin`.

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

### search

Renders a search bar that submits to a search engine or Wikipedia.

**Options:**

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `provider` | string | yes | - | Search provider: `"duckduckgo"` or `"wikipedia"` |
| `button_text` | string | no | "Search" | Text displayed on the search button and input placeholder |
| `results_in_new_tab` | boolean | no | false | Open search results in a new browser tab |
| `language` | string | no | "en" | Language code for Wikipedia (e.g., `"fr"`, `"de"`) |

**Examples:**

```yaml
cards:
  - title: Web Search
    plugin: search
    options:
      provider: duckduckgo
      button_text: "Search"

  - title: Wikipedia
    plugin: search
    options:
      provider: wikipedia
      language: fr
      button_text: "Wikipedia"
```

## Writing a Plugin

Create a directory under `src/plugins/` with an `__init__.py` and a plugin class:

```python
# src/plugins/myplugin/__init__.py
from src.plugin import Plugin

class MyPlugin(Plugin):
    def setup(self, options, database, scheduler, logger):
        pass

    def render(self, options):
        return "<p>Hello from my plugin!</p>"

    @staticmethod
    def validate_options(options, card_idx, filename):
        pass

    @staticmethod
    def setup_database(database):
        pass
```

The plugin will be automatically discovered and can be used with `plugin: myplugin` in your config.
