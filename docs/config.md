# Configuration

Salut is configured via a YAML file (`config.yml` or `starter.yaml`). The `config.yml` file takes precedence if both exist.

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

- **Type:** array (required)
- **Description:** Page layout columns containing cards

#### columns[].cards

- **Type:** array (required)
- **Description:** Cards within a column

#### columns[].cards[].title

- **Type:** string (required)
- **Description:** Card display title

#### columns[].cards[].type

- **Type:** string (required)
- **Description:** Card type (e.g., `newsfeed`, `search`, `weather`, `github`)

## Template Syntax

### Config Variables (`${...}`)

Resolved server-side from the config file:

| Variable | Description |
|----------|-------------|
| `${user_info.short_name}` | User's short name |
| `${user_info.long_name}` | User's full name |

### Client-Side Variables (`{{...}}`)

Resolved client-side by JavaScript:

| Variable | Description |
|----------|-------------|
| `{{time_emoji}}` | Time-based emoji (☀️ morning, 🌤️ afternoon, 🌙 evening, 🌑 night) |

### Server-Side Variables

Resolved server-side and passed to the template:

| Variable | Description |
|----------|-------------|
| `{{ datetime }}` | Localized long-form date (e.g., "Friday, June 05, 2026") |

## Example

```yaml
page_title: Salut
page_header: "Hi ${user_info.short_name} {{time_emoji}}"
language: en
user_info:
  short_name: Chris
  long_name: Chris P. Bacon

columns:
  - cards:
      - title: News
        type: newsfeed
        feeds:
          - https://news.ycombinator.com/rss
        count: 5
        schedule: "*/30 * * * *"
      - title: Search
        type: search
  - cards:
      - title: Weather
        type: weather
        city: Montreal
        units: metric
      - title: GitHub
        type: github
```
