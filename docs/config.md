# Configuration

Salut is configured via a YAML file (`config.yml` or `starter.yml`). The `config.yml` file takes precedence if both exist.

## Fields

### page_title

- **Type:** string (required)
- **Description:** Content for the HTML `<title>` tag
- **Example:** `Salut`

### page_header

- **Type:** string (required)
- **Description:** Greeting text displayed in the page header. Supports template variables for dynamic content. The template wraps this in a styled `<header>` element with an `<h1>` tag.
- **Default:** `Hi ${user_info.short_name} {{time_emoji}}`

### language

- **Type:** string (required)
- **Description:** Language code for date localization and the HTML `lang` attribute
- **Format:** BCP 47 tag (e.g., `en-US`, `fr-CA`) or simple language code (`en`, `fr`)
- **Defaults for simple codes:** `en` → `en-US`, `fr` → `fr-FR`

### user_info

- **Type:** object (required)
- **Description:** User identity information used in greetings

#### user_info.short_name

- **Type:** string (required)
- **Description:** Short display name used in greetings
- **Example:** `Chris`

#### user_info.long_name

- **Type:** string (required)
- **Description:** Full display name
- **Example:** `Chris P. Bacon`

### columns

- **Type:** integer (required)
- **Description:** Number of columns in the page layout
- **Example:** `3`

### cards

- **Type:** array (required)
- **Description:** Flat list of cards that auto-flow left-to-right across columns

#### cards[].title

- **Type:** string (required)
- **Description:** Card display title

#### cards[].plugin

- **Type:** string (required)
- **Description:** Plugin name to render card content (see [Plugins](plugins/))
- **Example:** `html`

#### cards[].options

- **Type:** object (optional)
- **Description:** Plugin-specific options

#### cards[].colspan

- **Type:** integer (optional, default: 1)
- **Description:** Number of columns this card spans

#### cards[].options

- **Type:** object (optional)
- **Description:** Plugin-specific options

For the `rss` plugin, see [Plugins](plugins/) for available options.

## Template Syntax

### Config Variables (`${...}`)

Resolved server-side from the config file. Works in any string value (titles, options, headers, etc.):

| Variable | Description |
|----------|-------------|
| `${user_info.short_name}` | User's short name |
| `${user_info.long_name}` | User's full name |

### Client-Side Variables (`{{...}}`)

Resolved client-side by JavaScript in the rendered HTML:

| Variable | Description |
|----------|-------------|
| `{{time_emoji}}` | Time-based emoji (☀️ morning, 🌤️ afternoon, 🌙 evening, 🌑 night) |
| `{{date}}` | Localized long-form date (e.g., "Friday, June 05, 2026") |
| `{{theme_toggle}}` | Light/dark theme toggle button (sun/moon SVG icons) |

## Example

```yaml
page_title: Salut
page_header: "<h1>Hi ${user_info.short_name} {{time_emoji}}</h1><span>{{date}} {{theme_toggle}}</span>"
language: en
user_info:
  short_name: Chris
  long_name: Chris P. Bacon

columns: 3

cards:
  - title: Welcome
    plugin: html
    options:
      html: "<p>Welcome to Salut!</p>"
  - title: Links
    plugin: html
    options:
      html: "<ul><li><a href='https://github.com'>GitHub</a></li></ul>"
  - title: About
    plugin: html
    colspan: 2
    options:
      html: "<p>Salut means Hi in French.</p>"
```
