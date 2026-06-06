## Context

Cards are currently hardcoded placeholders with no rendering logic. The template shows `{{ card.type }} card (coming soon)` for each card. We need a plugin system where each card type is a self-contained module that renders its own content. The `html` plugin will be the first implementation, allowing users to render arbitrary HTML.

## Goals / Non-Goals

**Goals:**
- Plugin-based card architecture with a `plugins/` directory
- Each plugin in its own subdirectory
- Plugin discovery and rendering
- `html` plugin that renders hardcoded HTML from config
- `colspan` support for cards spanning multiple columns

**Non-Goals:**
- Dynamic plugin loading (plugins are statically known)
- Plugin API versioning
- Third-party plugin installation
- Other plugin types (newsfeed, weather, etc.) — future work

## Decisions

### 1. Plugin directory structure

**Decision:** Each plugin lives in `src/plugins/<plugin-name>/` with an `__init__.py` that exposes a `render(options)` function.

```
src/plugins/
  html/
    __init__.py   # def render(options) -> str
```

**Rationale:**
- Simple, Pythonic structure
- Each plugin is self-contained
- Easy to add new plugins later
- `__init__.py` makes imports clean: `from src.plugins.html import render`

**Alternatives considered:**
- Single file per plugin: Rejected because plugins may grow (templates, helpers)
- Class-based plugins: Overkill for now, functions are simpler

### 2. Plugin rendering approach

**Decision:** Plugins are called server-side in `main.py`, results passed to template as a dict mapping card indices to rendered HTML.

**Rationale:**
- Keeps template simple (just `{{ card_content[index] | safe }}`)
- Plugins can do any server-side logic (API calls, DB queries)
- No client-side JavaScript needed for basic plugins

**Alternatives considered:**
- Client-side rendering: Rejected because it requires JavaScript per plugin
- Template inheritance per plugin: Complex, harder to maintain

### 3. Config schema for cards

**Decision:** Cards use a flat list at the top level, with `columns` specifying the number of columns as an integer. Each card has `plugin` (string), `options` (dict), and optional `colspan` (int, default 1).

```yaml
columns: 3
cards:
  - title: My HTML Card
    plugin: html
    colspan: 2
    options:
      html: "<p>Hello world</p>"
```

**Rationale:**
- Flat list is simpler than nested columns
- Auto-flow left-to-right is intuitive — users just list cards in order
- `colspan` allows cards to span columns when needed
- `columns` as a number is clearer than inferring from array length

**Alternatives considered:**
- Nested columns array: Rejected as unnecessarily complex for auto-flow layout

### 4. Colspan implementation

**Decision:** Use CSS grid with `grid-template-columns` and `col-span-N` classes.

**Rationale:**
- Tailwind has built-in colspan utilities
- Works with dynamic column counts
- Simple to implement

## Risks / Trade-offs

- **HTML injection**: Users can put arbitrary HTML in config → Mitigated by being a self-hosted single-user app (user controls their own config)
- **Plugin errors**: A broken plugin could crash the page → Mitigated by try/except in plugin loading with fallback to error message
