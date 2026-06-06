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
- **Description:** Plugin-specific options. See plugin documentation for available options:
  - [HTML](plugins/html.md)
  - [RSS](plugins/rss.md)
  - [Search](plugins/search.md)
  - [Weather](plugins/weather.md)
  - [Calendar](plugins/calendar.md)

#### cards[].colspan

- **Type:** integer (optional, default: 1)
- **Description:** Number of columns this card spans

## Secrets

`secrets.yml` is an optional file for storing sensitive values like passwords and tokens. Reference them in your config using `${secrets.key}` syntax:

```yaml
# secrets.yml
calendar_password: "my-s3cur3-p@ss"
```

```yaml
# config.yml
cards:
  - title: Calendar
    plugin: calendar
    options:
      calendars:
        - url: https://caldav.example.com/user/cal1/
          name: Personal
          auth_type: basic
          username: user
          password: ${secrets.calendar_password}
```

If a secret key is not found, the variable resolves to an empty string.

## Template Syntax

### Config Variables (`${...}`)

Resolved server-side from the config file. Works in any string value (titles, options, headers, etc.):

| Variable | Description |
|----------|-------------|
| `${user_info.short_name}` | User's short name |
| `${user_info.long_name}` | User's full name |
| `${secrets.key}` | Value from `secrets.yml` (see [Secrets](#secrets)) |
| `${i18n.key}` | Translated string from i18n files |

### Client-Side Variables (`{{...}}`)

Resolved client-side by JavaScript in the rendered HTML:

| Variable | Description |
|----------|-------------|
| `{{time_emoji}}` | Time-based emoji (☀️ morning, 🌤️ afternoon, 🌙 evening, 🌑 night) |
| `{{date}}` | Localized long-form date (e.g., "Friday, June 05, 2026") |
| `{{theme_toggle}}` | Light/dark theme toggle button (sun/moon SVG icons) |

## Example

See [starter.yml](../starter.yml) for an example configuration.
