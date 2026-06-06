# Plugins

Plugins render card content. Each plugin lives in `src/plugins/<name>/` and extends the abstract `Plugin` class in `src/plugin.py`.

## Plugin Architecture

Each plugin is a class that extends `Plugin` with these methods and properties:

- `card_style_rules()` — Static method returning a `dict[str, str]` mapping sub-selectors to CSS declarations. Keys are relative to the card's CSS class (e.g. `"img"` becomes `.html-card img`). Returns an empty dict by default; override only if custom styling is needed.
- `setup(options, database, scheduler, logger)` — Initialize the plugin for a card. Called once at startup.
- `render(options)` — Return HTML string for the card.
- `validate_options(options, card_idx, filename)` — Validate plugin-specific options. Raise `ConfigError` if invalid.
- `init_schema(database)` — Initialize database tables for this plugin. Called once at startup.

Plugins are automatically discovered by scanning `src/plugins/<name>/` for classes that extend `Plugin`.

## Available Plugins

- [HTML](html.md) — Renders arbitrary HTML
- [RSS](rss.md) — Fetches and displays RSS feed items
- [Search](search.md) — Search bar for DuckDuckGo or Wikipedia
- [Weather](weather.md) — Current weather conditions from Open-Meteo
- [Calendar](calendar.md) — Upcoming calendar events from CalDAV or ICS

## Writing a Plugin

Create a directory under `src/plugins/` with an `__init__.py` and a plugin class:

```python
# src/plugins/myplugin/__init__.py
from src.plugin import Plugin

class MyPlugin(Plugin):
    @staticmethod
    def card_style_rules() -> dict[str, str]:
        return {
            "img": "max-width: 100%; height: auto;",
        }

    def setup(self, options, database, scheduler, logger):
        pass

    def render(self, options):
        return "<p>Hello from my plugin!</p>"

    @staticmethod
    def validate_options(options, card_idx, filename):
        pass

    @staticmethod
    def init_schema(database):
        pass
```

The plugin will be automatically discovered and can be used with `plugin: myplugin` in your config.
