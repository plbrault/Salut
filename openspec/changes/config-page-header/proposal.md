## Why

The current config uses a generic `title` field for both the HTML `<title>` tag and the page heading. Users need a way to personalize their starter page with their name and a dynamic greeting based on time of day. This makes the page feel more welcoming and tailored to the individual.

## What Changes

- Rename `title` to `page_title` in the config schema
- Add `page_header` field to control the `<h1>` content (supports template variables)
- Add `user_info` dictionary with `short_name` and `long_name`
- Add dynamic time emoji via inline JavaScript (☀️ morning, 🌤️ afternoon, 🌙 evening, 🌑 night)
- Two template syntaxes: `${...}` for YAML config variables, `{{...}}` for HTMX-fetched values
- Default `page_header`: `Salut ${user_info.short_name} {{time_emoji}}`

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `config-loading`: Config schema changes (new required fields, renamed field)

## Impact

- `starter.yaml` — schema update
- `app/config.py` — validation changes
- `app/template.py` — new module for template resolution
- `app/main.py` — use template resolver
- `app/templates/index.html` — use new config fields, inline JS for time emoji
- `tests/test_config.py` — update tests for new schema
- `tests/test_template.py` — new tests for template resolver
- `tests/test_server.py` — update tests for new template
