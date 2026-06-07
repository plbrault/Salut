# Image Plugin

Displays a single image from an RSS feed, REST API, or local file. The image is cached server-side with dimensions extracted from file headers to prevent layout shift.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `provider_type` | string | yes | - | `rss`, `rest`, or `file` |
| `url` | string | yes | - | Feed URL, API endpoint, or file path relative to `/static/custom/` |
| `request_method` | string | no | `GET` | HTTP method for REST provider (`GET` or `POST`) |
| `schedule` | string | no | - | Cron expression for refresh schedule. If absent, fetches on every page load |
| `footer_html` | string | no | - | Custom HTML rendered below the image (e.g., "Powered by" links) |

## Examples

### RSS Feed

```yaml
cards:
  - title: Work Chronicles
    plugin: image
    options:
      provider_type: rss
      url: "https://www.workchronicles.com/feed"
```

### REST API

```yaml
cards:
  - title: Random Cat
    plugin: image
    options:
      provider_type: rest
      url: "https://cataas.com/cat?width=400"
      footer_html: "Powered by <a href='https://cataas.com' target='_blank' rel='noopener' style='color: var(--link)'>CATAAS</a>"
```

### Local File

```yaml
cards:
  - title: My Logo
    plugin: image
    options:
      provider_type: file
      url: "logo.png"
```

## Features

- Three provider types: RSS, REST, and file
- Server-side image caching (one file per card)
- Image dimensions extracted from PNG/JPEG headers (no layout shift)
- Clickable image linking to the source page
- Optional footer HTML for custom content
- Optional schedule; if absent, fetches on every page load
