# Themes

Themes control the visual tokens of your start page: colors, font family, and card border radius. Each theme is a directory under `src/themes/` containing a `theme.yml` file, plus an optional `static/` subdirectory for servable font assets.

## Selecting a theme

Use the `theme` field in your config file (see [Configuration](config.md#theme)):

```yaml
# One theme for both modes; the theme toggle is disabled
theme: default-light

# One theme per mode; the theme toggle switches between them
theme:
  light: default-light
  dark: default-dark
```

If the field is omitted, the default pair `{ light: default-light, dark: default-dark }` is used.

The page still switches modes with `data-theme="light"` and `data-theme="dark"`; your config only decides which theme supplies the variables for each mode.

## Theme directory structure

```
src/themes/
├── default-light/
│   ├── theme.yml
│   └── static/
│       ├── fonts.css
│       ├── Inter-Variable.woff2
│       └── Inter-License.txt
└── default-dark/
    └── theme.yml
```

A theme is discovered when its directory contains a `theme.yml` file. The directory name is the name used in the config.

Only the `static/` subdirectory is served under `/themes/<theme-name>/`. Files outside `static/` (such as `theme.yml` and Python modules) are not accessible via HTTP.

## theme.yml

```yaml
name: "Default Light"       # optional display name
extends: default-light      # optional parent theme

colors:
  bg: "#f3f4f6"
  card_bg: "white"
  text: "#111827"
  text_muted: "#6b7280"
  text_faint: "#9ca3af"
  border: "#e5e7eb"
  link: "#2563eb"
  link_hover: "#1d4ed8"
  code_bg: "#f3f4f6"

fonts:
  family: "'Inter', sans-serif"

radius:
  card: "0.5rem"
```

### Required values

Every resolved theme must provide all of these values, either directly or through inheritance:

| Section | Key | CSS variable |
|---------|-----|--------------|
| `colors` | `bg` | `--bg` |
| `colors` | `card_bg` | `--card-bg` |
| `colors` | `text` | `--text` |
| `colors` | `text_muted` | `--text-muted` |
| `colors` | `text_faint` | `--text-faint` |
| `colors` | `border` | `--border` |
| `colors` | `link` | `--link` |
| `colors` | `link_hover` | `--link-hover` |
| `colors` | `code_bg` | `--code-bg` |
| `fonts` | `family` | `--font-family` |
| `radius` | `card` | `--card-radius` |

A theme that is missing a required value is rejected when the config is validated.

## Inheritance

A theme can extend another theme and override only the values it cares about:

```yaml
# src/themes/sunset/theme.yml
extends: default-light

colors:
  bg: "#fff7f5"
  link: "#d97706"
```

- The child inherits all sections (`colors`, `fonts`, `radius`) from its parent.
- Within a section, child keys override (or add to) the parent's keys.
- `name` and `extends` are not inherited.
- Multi-level inheritance is supported. Circular inheritance is rejected with an error.

## Fonts

A theme can bundle its own font files and declare them in a `fonts.css` file placed in the theme's `static/` subdirectory:

```css
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
  src: url('Inter-Variable.woff2') format('woff2');
}
```

Font files are referenced relative to the `fonts.css` file itself. The `static/` subdirectory is served under `/themes/<theme-name>/`, so the example above resolves to `/themes/<theme-name>/Inter-Variable.woff2`.

At render time, the page includes a `<link>` tag for every `fonts.css` found in the inheritance chains of the active light and dark themes, so a child theme automatically picks up its parent's fonts.

## Built-in themes

- `default-light` — the original light palette, bundles the Inter font in `static/`.
- `default-dark` — extends `default-light` and overrides only the colors.

The configuration error page always uses the built-in themes, since the configured theme may be the very thing that failed to load.

## What is not themable

Only colors, font family, and card border radius come from themes. The masonry layout algorithm, card structure, responsive breakpoints, padding, gaps, and font sizes stay hardcoded. Extra keys in `theme.yml` are ignored by the layout.
