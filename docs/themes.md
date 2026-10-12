# Themes

Themes control the visual tokens of your start page: colors, fonts, and card border radius. Each theme is a directory under `src/themes/` containing a `theme.yml` file, plus an optional `static/` subdirectory for servable font assets and custom CSS/JavaScript files.

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
  accent: "#2563eb"
  accent_hover: "#1d4ed8"
  accent_contrast: "#ffffff"
  danger: "#dc2626"
  danger_hover: "#b91c1c"
  danger_contrast: "#ffffff"

fonts:
  page_heading: "'Inter', sans-serif"   # page header and admin/error headings
  card_heading: "'Inter', sans-serif"   # card titles
  card_content: "'Inter', sans-serif"   # body and card content text

radius:
  card: "0.5rem"
```

### includes (optional)

A theme can declare custom CSS and JavaScript files to load. These files are placed in the theme's `static/` subdirectory and served under `/themes/<theme-name>/`.

```yaml
includes:
  css:                    # list of CSS files, inlined as <style> blocks
    - "theme.css"
  js:                     # list of JS files, loaded as <script type="module">
    - "theme.js"
```

**Validation:**
- `includes` is optional
- `css` and `js` must be arrays of strings (paths relative to `static/`)
- All listed files must exist in the theme's `static/` directory

**Inheritance behavior:** Child themes do NOT inherit parent's `includes`. Each theme must declare its own `includes` if it wants custom CSS/JS files loaded.

**Mode behavior:** With a `{ light, dark }` theme pair, both themes' CSS files are inlined in the page as `<style data-theme-include="light|dark">` blocks and the browser enables only the set that matches the active mode. Inlining keeps first paint free of extra stylesheet round trips. The active mode's JS modules are loaded at page load; since ES module effects cannot be torn down, switching modes on a theme that declares JS includes reloads the page so the correct mode's scripts run.

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
| `colors` | `accent` | `--accent` |
| `colors` | `accent_hover` | `--accent-hover` |
| `colors` | `accent_contrast` | `--accent-contrast` |
| `colors` | `danger` | `--danger` |
| `colors` | `danger_hover` | `--danger-hover` |
| `colors` | `danger_contrast` | `--danger-contrast` |
| `fonts` | `page_heading` | `--font-page-heading` |
| `fonts` | `card_heading` | `--font-card-heading` |
| `fonts` | `card_content` | `--font-card-content` |
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

Each theme defines three font roles: `page_heading` (page header and admin/error headings), `card_heading` (card titles), and `card_content` (body and card content text). Set them to the same value for a uniform look, or to different families for distinct typographic voices. Like colors, each role can be overridden independently by a child theme.

A theme can bundle its own font files and declare them in a `fonts.css` file placed in the theme's `static/` subdirectory. A single `fonts.css` may contain multiple `@font-face` rules so each role can reference a different bundled family:

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

At render time, the contents of every `fonts.css` found in the inheritance chains of the active light and dark themes are inlined into the page head (with relative URLs rewritten to their absolute `/themes/<theme-name>/...` paths), so a child theme automatically picks up its parent's fonts without extra stylesheet requests.

## Custom CSS and JavaScript

A theme can include custom CSS and JavaScript files to add visual effects, background images, animations, or interactive elements. Files are declared in the `includes` section of `theme.yml` and placed in the theme's `static/` subdirectory.

### theme.js

A theme's JavaScript file (declared in `includes.js`) is loaded as an ES module (`<script type="module">`) at the end of `<body>`. It executes immediately on load as a standard ES module. No special contract is required — themes can use standard browser APIs.

### Asset References

CSS files in `static/` can reference sibling assets (images, fonts) using relative URLs. Since theme CSS is inlined into the page, the server rewrites these to absolute paths at render time:

```css
/* theme.css */
.halloween-bg {
    background-image: url("pumpkin.svg");  /* resolves to /themes/halloween/pumpkin.svg */
}
```
