# Search Plugin

Renders a search bar that submits to a search engine or Wikipedia.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `provider` | string | yes | - | Search provider: `"duckduckgo"` or `"wikipedia"` |
| `button_text` | string | no | i18n `"search"` key | Text displayed on the search button and input placeholder |
| `placeholder_text` | string | no | i18n `"search"` key | Placeholder text for the search input |
| `results_in_new_tab` | boolean | no | false | Open search results in a new browser tab |
| `language` | string | no | "en" | Language code for Wikipedia (e.g., `"fr"`, `"de"`) |

## Examples

```yaml
cards:
  - title: Web Search
    plugin: search
    options:
      provider: duckduckgo

  - title: Wikipedia
    plugin: search
    options:
      provider: wikipedia
      language: fr
      button_text: "Wikipedia"
```
