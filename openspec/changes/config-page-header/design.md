## Context

The Salut starter page currently uses a single `title` field for both the HTML `<title>` tag and the page heading. Users want to personalize their page with their name and a dynamic greeting based on time of day. The config schema needs to be extended to support this personalization.

## Goals / Non-Goals

**Goals:**
- Allow users to personalize the page header with their name
- Provide a dynamic time emoji based on time of day
- Support template variables in the page header string
- Support localized datetime display
- Support HTML lang attribute from config
- Simple, clean config schema (no legacy compatibility concerns)

**Non-Goals:**
- Support for arbitrary template variables (only `${user_info.short_name}` for config refs, `{{time_emoji}}` for client-side)
- Custom emoji configuration
- User-customizable header HTML structure

## Decisions

### 1. Time emoji logic
**Decision:** Implement as a small inline JavaScript snippet that replaces `{{time_emoji}}` with the correct emoji based on `new Date().getHours()`.

**Rationale:**
- Simplest possible implementation
- No server-side logic or endpoints needed
- Always uses the user's local time
- No HTMX dependency for this feature

**Alternatives considered:**
- HTMX endpoint: Rejected because it adds unnecessary complexity
- Server-side (using server time): Rejected because it would be wrong if server timezone differs
- Jinja2 filter: Rejected because it would require custom Jinja2 setup

**Emoji mapping:**
- 6:00–11:59 → ☀️ (sun)
- 12:00–17:59 → 🌤️ (sun behind cloud)
- 18:00–21:59 → 🌙 (moon)
- 22:00–5:59 → 🌑 (new moon)

### 2. Template variable syntax
**Decision:** Use two distinct syntaxes for different variable sources:
- `${user_info.short_name}` — references values from the YAML config itself (resolved server-side)
- `{{time_emoji}}` — replaced by inline JavaScript with the correct emoji

**Rationale:**
- Clear distinction between config references and dynamic values
- `${...}` is a common shell/variable syntax, intuitive for config refs
- `{{...}}` is a common template syntax, intuitive for dynamic content
- Server resolves config refs, client replaces dynamic markers

**Alternatives considered:**
- Same syntax for both: Rejected because it hides the source of the value
- `${}` for config, `%{}` for computed: Rejected because `%{}` is less recognizable
- `${}` for config, `#{}` for computed: Rejected because `#{}` is associated with Ruby/interpolation

### 3. Config validation
**Decision:** Require `page_title`, `page_header`, `language`, `user_info.short_name`, and `user_info.long_name`.

**Rationale:**
- All fields are needed for the feature to work
- Clear error messages if fields are missing
- Consistent with existing validation pattern

**Alternatives considered:**
- Make fields optional with defaults: Rejected because it would hide config errors

### 4. Template resolver
**Decision:** Implement a template resolver in `app/template.py` that processes `${...}` syntax by resolving config references from the config dict. The `{{time_emoji}}` syntax is left for inline JavaScript to replace client-side.

**Rationale:**
- Clear separation of concerns: config refs resolved server-side, dynamic values handled client-side
- Template logic isolated in `app/template.py`, not mixed into `app/main.py`
- No need to pass context dict to template resolver
- Easy to test config resolution independently

**Alternatives considered:**
- Pass raw config and process in template: Rejected because it would complicate the template

### 5. Language validation
**Decision:** Accept BCP 47 tags (e.g., `en-US`, `fr-CA`) or simple language codes (`en`, `fr`) with automatic normalization to BCP 47 defaults.

**Rationale:**
- BCP 47 is the standard for language tags
- Simple codes are more user-friendly
- Defaults: `en` → `en-US`, `fr` → `fr-FR`

### 6. Localized datetime
**Decision:** Implement as a client-side JavaScript snippet using `Intl.DateTimeFormat` with the browser's language (from `<html lang>`).

**Rationale:**
- Always uses the user's local time and timezone
- Uses the same language as the HTML lang attribute
- Simple implementation, no server-side logic needed

**Alternatives considered:**
- Server-side datetime: Rejected because it uses server timezone, not user's local time

### 7. Header styling
**Decision:** Config `page_header` contains HTML structure but no CSS classes. Template wraps content in `<header>` and applies styling via a `<style>` block targeting semantic selectors (`header h1`, `header > *:not(h1)`).

**Rationale:**
- Tailwind can't scan YAML files for class names
- Config stays focused on content, not presentation
- CSS selectors work regardless of what HTML elements users put in page_header
- Users can customize HTML structure (e.g., add `<nav>`, `<p>`) without worrying about styling

**Alternatives considered:**
- Tailwind classes in config: Rejected because Tailwind can't compile classes from YAML
- Inline styles in template: Rejected because it would be less maintainable

### 8. HTML lang attribute
**Decision:** Set `<html lang="{{ language }}">` from the validated/normalized language config value.

**Rationale:**
- Proper HTML semantics
- Helps browsers and screen readers
- Consistent with the language config

## Risks / Trade-offs

- (none — initial dev, no legacy users)
- **Hardcoded emoji**: Users cannot customize the emoji. Mitigation: This is a non-goal for now, but can be added later.
- **Server-side datetime**: Uses server timezone, not user's local time. Mitigation: Date rarely differs across timezones, and this is a single-user app.

## Example Config

```yaml
page_title: Salut
page_header: "<h1>Hi ${user_info.short_name} {{time_emoji}}</h1><span>{{datetime}}</span>"
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

**Renders as:**
```html
<html lang="en-US">
<head><title>Salut</title>
    <style>
        header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }
        header h1 {
            font-size: 2.5rem;
            font-weight: bold;
        }
        header span {
            font-size: 1.125rem;
            font-weight: 500;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <header>
        <h1>Hi Chris ☀️</h1> Friday, June 05, 2026
    </header>
    <!-- cards -->
</body>
</html>
```
