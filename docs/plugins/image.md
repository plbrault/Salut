# Image Plugin

Displays a single image from an RSS feed, REST API, or local file. The image is cached server-side with dimensions extracted from file headers to prevent layout shift.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `provider_type` | string | yes | - | `rss`, `rest`, or `file` |
| `url` | string | yes | - | Feed URL, API endpoint, or file path relative to `/static/custom/` |
| `request_method` | string | no | `GET` | HTTP method for REST provider (`GET` or `POST`) |
| `schedule` | string | no | - | Cron expression for refresh schedule. If absent, fetches a new image on every page load (see notes below) |
| `footer_html` | string | no | - | Custom HTML rendered below the image (e.g., "Powered by" links) |

## Schedule Behavior

When `schedule` is **not set**:
- A new image is fetched on every page load
- The image is **not** cached server-side
- The remote URL is passed directly to the browser
- Image dimensions are **not** extracted, so **layout shift may occur** until the image loads
- An `onload` handler is used to mitigate layout shift

When `schedule` **is set**:
- The image is cached server-side after fetching
- Image dimensions are extracted from PNG/JPEG headers to prevent layout shift
- The cached image is served as a local file

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
- Server-side image caching with dimensions extraction (when `schedule` is set)
- Clickable image linking to the source page
- Optional footer HTML for custom content
- Optional schedule; if absent, fetches on every page load without caching
