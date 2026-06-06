## Why

Cards currently use hardcoded placeholder content with no actual rendering logic. To build a useful starter page, we need a plugin system where each card type is a self-contained plugin that renders its own content. The first plugin (`html`) will allow users to render arbitrary HTML content in cards.

Additionally, the current nested `columns` config structure is unnecessarily complex. Cards should be a flat list that auto-flows left-to-right, with `columns` specifying only the number of columns.

## What Changes

- **BREAKING**: Replace current card config schema (`type`, `feeds`, `count`, etc.) with plugin-based schema (`plugin`, `options`, `colspan`)
- **BREAKING**: Replace nested `columns` array with a flat `cards` list and a numeric `columns` field
- Create `src/plugins/` directory with plugin architecture
- Implement `html` plugin that renders hardcoded HTML from config
- Update template to render plugin content instead of placeholder text
- Cards auto-flow left-to-right across columns, with `colspan` support

## Capabilities

### New Capabilities

- `card-plugins`: Plugin-based card rendering system with plugin discovery and execution

### Modified Capabilities

- `config-loading`: Config schema changes — `columns` is now an integer, `cards` is a flat top-level list

## Impact

- `src/plugins/` — new directory with plugin architecture
- `src/main.py` — load and pass plugins to template, auto-flow grid layout
- `src/templates/index.html` — render plugin content
- `starter.yml` — flat cards structure
- `src/config.py` — updated validation (columns=int, cards=flat list)
