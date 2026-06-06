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

## Writing a Plugin

Create a directory under `src/plugins/` with an `__init__.py`:

```python
# src/plugins/myplugin/__init__.py

def render(options):
    # Return an HTML string
    return "<p>Hello from my plugin!</p>"
```

The plugin will be automatically discovered and can be used with `plugin: myplugin` in your config.
