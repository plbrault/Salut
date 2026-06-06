# HTML Plugin

Renders arbitrary HTML from the card's `options.html` field.

## Options

| Option | Type | Description |
|--------|------|-------------|
| `html` | string | HTML content to render |

## Example

```yaml
cards:
  - title: My Card
    plugin: html
    options:
      html: "<p>Hello world!</p>"
```

If no `html` option is provided, the card renders empty content.
