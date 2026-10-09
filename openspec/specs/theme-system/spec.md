# Theme System

## Purpose

Provides a configurable, extensible theme system for Salut. Visual tokens such as colors, fonts, and border radius are defined in YAML theme files under `src/themes/`. Users select themes via the config file, and themes can inherit from parent themes to create variations without duplication.

## Requirements

### Requirement: Themes are defined in YAML files

Each theme SHALL be a directory under `src/themes/` containing a `theme.yml` file. The file SHALL define `colors`, `fonts`, and `radius` sections using snake_case keys. Optional `name` and `extends` fields MAY be present.

#### Scenario: Built-in default light theme

- **WHEN** the `default-light` theme is loaded
- **THEN** it provides values for `--bg`, `--card-bg`, `--text`, `--text-muted`, `--text-faint`, `--border`, `--link`, `--link-hover`, `--code-bg`, `--font-family`, and `--card-radius`

#### Scenario: Built-in default dark theme inherits from default-light

- **GIVEN** the `default-dark` theme declares `extends: default-light`
- **WHEN** the `default-dark` theme is resolved
- **THEN** it inherits `fonts.family` and `radius.card` from `default-light` and overrides only the color values

### Requirement: Themes can inherit from parent themes

A theme MAY declare `extends: <parent-name>`. The child theme SHALL inherit all sections from the parent and override only the keys it explicitly defines. Multi-level inheritance SHALL be supported. Circular inheritance SHALL raise a config error.

#### Scenario: Child theme overrides background and link colors

- **GIVEN** a theme `pastel-light` with `extends: default-light` that only sets `colors.bg` and `colors.link`
- **WHEN** `pastel-light` is resolved
- **THEN** it uses `default-light` values for all properties except `bg` and `link`

#### Scenario: Circular inheritance is rejected

- **GIVEN** theme `a` extends `b` and theme `b` extends `a`
- **WHEN** the config references theme `a`
- **THEN** config validation raises an error about circular theme inheritance

### Requirement: Config selects single theme or light/dark pair

The config SHALL support a `theme` field that is either a string naming a single theme, or a mapping with `light` and `dark` keys naming two themes. A single theme SHALL apply to both light and dark modes. If omitted, the default SHALL be `{ light: default-light, dark: default-dark }`.

#### Scenario: Single theme config

- **GIVEN** `theme: default-light`
- **WHEN** the page renders
- **THEN** both light and dark modes use the `default-light` palette

#### Scenario: Light/dark pair config

- **GIVEN** `theme: { light: default-light, dark: default-dark }`
- **WHEN** the page renders
- **THEN** light mode uses `default-light` and dark mode uses `default-dark`

### Requirement: Mode remains independent of theme name

The HTML `data-theme` attribute SHALL continue to hold only `"light"` or `"dark"`. The config SHALL determine which resolved theme supplies the variables for each mode. Components and plugins SHALL continue consuming semantic CSS variables and SHALL NOT depend on specific theme names.

#### Scenario: Toggle switches mode, not theme name

- **GIVEN** a two-theme config
- **WHEN** the user clicks the theme toggle
- **THEN** `data-theme` flips between `"light"` and `"dark"`, and the corresponding theme variables apply

### Requirement: Theme toggle respects single-theme mode

When only one theme is configured, the `{{theme_toggle}}` variable SHALL still render a button, but the button SHALL be disabled and not switch modes.

#### Scenario: Single theme greys out toggle

- **GIVEN** `theme: default-light`
- **WHEN** the page renders
- **THEN** the theme toggle button is visible but disabled

### Requirement: Themes can include local font files

A theme directory MAY contain font files (e.g., `.woff2`) and a `fonts.css` file with `@font-face` rules referencing them. The server SHALL serve theme directories statically and include any `fonts.css` files from the active themes' inheritance chains in the rendered page.

#### Scenario: Built-in theme references bundled Inter font

- **GIVEN** `default-light` contains `Inter-Variable.woff2` and a `fonts.css` referencing it, and `default-dark` extends `default-light`
- **WHEN** the page renders with the default light/dark config
- **THEN** the Inter font face is loaded for both modes via the `default-light` inheritance chain

### Requirement: Layout is not themable

The masonry layout algorithm, card structure, responsive breakpoints, padding, gaps, and font sizes SHALL remain hardcoded. Only colors, font family, and card border radius are controlled by themes.

#### Scenario: Card radius is themable

- **GIVEN** a theme sets `radius.card: 1rem`
- **WHEN** cards render
- **THEN** cards use `1rem` border radius

#### Scenario: Masonry gap is not themable

- **GIVEN** a theme attempts to define spacing or gap tokens
- **WHEN** the theme is loaded
- **THEN** those tokens are ignored by the layout JavaScript and CSS

### Requirement: Admin page uses the configured theme

The admin page SHALL receive the same generated theme CSS as the main page, since the config is valid when the admin panel is accessible. The admin page SHALL continue to use its own layout-specific CSS, but color and font tokens SHALL come from the active theme.

#### Scenario: Admin page reflects user theme

- **GIVEN** the user configures a custom light/dark theme pair
- **WHEN** the admin page renders
- **THEN** it uses the same colors and font as the main page

### Requirement: Error page uses a built-in theme fallback

The config error page SHALL receive generated CSS from the built-in `default-light`/`default-dark` themes, since the configured theme may be invalid when the error page renders. Error-specific variables (e.g., error background, border, text) MAY remain hardcoded in the error template.

#### Scenario: Error page renders despite invalid theme config

- **GIVEN** the config contains an invalid `theme` value
- **WHEN** the error page renders
- **THEN** it still applies a usable light/dark color scheme using the built-in defaults

### Requirement: Theme CSS is generated server-side

The server SHALL read the configured themes, resolve inheritance, validate required keys, and generate a `<style>` block containing CSS custom properties for `:root`, `[data-theme="light"]`, and `[data-theme="dark"]`. The generated CSS SHALL be cached in app state and regenerated on config reload.

#### Scenario: Config reload updates theme

- **GIVEN** the admin panel saves a new `theme` value
- **WHEN** `reload_app_state()` runs
- **THEN** the generated theme CSS reflects the new configuration

### Requirement: Validation catches invalid theme configuration

Config validation SHALL reject:
- A `theme` value that is neither a string nor a `{ light, dark }` mapping
- Missing or empty theme names
- References to theme directories that do not exist
- Themes missing a `theme.yml` file
- Circular inheritance
- Resolved themes missing required `colors`, `fonts`, or `radius` keys

#### Scenario: Missing theme directory

- **GIVEN** `theme: nonexistent`
- **WHEN** config is validated
- **THEN** validation raises an error indicating the theme was not found
