# Design: Theme Visual Effects

## Overview

Add an `includes` section to `theme.yml` for declaring CSS and JavaScript files. Extend the theme loader to parse `includes`, generate URLs, and pass them to the template. Update `index.html` to inject the declared files.

## Theme Vocabulary Changes

### Updated `theme.yml` Schema

```yaml
# Optional new section
includes:
  css: [string]      # paths relative to theme static/, loaded as <link rel="stylesheet">
  js: [string]       # paths relative to theme static/, loaded as <script type="module">
```

**Validation:**
- `includes` is optional
- `css` and `js` are arrays of strings (relative paths)
- Files must exist in theme's `static/` directory (validated at load time)

### Theme Loader Changes (`src/themes/__init__.py`)

```python
# In load_theme(): parse and store includes
def load_theme(name, themes_dir=None):
    # ... existing ...
    data = yaml.safe_load(file)
    includes = data.get("includes")
    if includes is not None:
        if not isinstance(includes, dict):
            raise ThemeError(f"Theme '{name}': 'includes' must be a mapping.")
        # Validate structure
        for key in ("css", "js"):
            val = includes.get(key)
            if val is not None and not isinstance(val, list):
                raise ThemeError(f"Theme '{name}': 'includes.{key}' must be a list.")
            if val:
                for item in val:
                    if not isinstance(item, str):
                        raise ThemeError(f"Theme '{name}': 'includes.{key}' items must be strings.")
        # Validate file existence
        static_dir = theme_static_dir(name, themes_dir)
        for css_file in includes.get("css", []):
            if not (static_dir / css_file).is_file():
                raise ThemeError(f"Theme '{name}': CSS file not found: {css_file}")
        for js_file in includes.get("js", []):
            if not (static_dir / js_file).is_file():
                raise ThemeError(f"Theme '{name}': JS file not found: {js_file}")
    # Store in returned data
    if includes:
        data["includes"] = includes
    return data

# In resolve_theme(): child themes do NOT inherit parent's includes
# Any inherited includes are explicitly removed
# This is intentional — effects don't layer cleanly

# In generate_theme_css(): return includes info
def generate_theme_css(theme_config, themes_dir=None):
    # ... existing ...
    selection = normalize_theme_config(theme_config)
    light = load_resolved_theme(selection["light"], themes_dir)
    dark = load_resolved_theme(selection["dark"], themes_dir)

    # Get includes from resolved themes (only the final theme in chain)
    light_includes = light.get("includes", {})
    dark_includes = dark.get("includes", {})

    css = "\n\n".join([
        _render_block([':root', '[data-theme="light"]'], light),
        _render_block(['[data-theme="dark"]'], dark),
    ])
    font_links = font_css_links([selection["light"], selection["dark"]], themes_dir)
    
    # Build absolute URLs for includes
    def build_urls(includes, theme_name):
        css_urls = [f"/themes/{theme_name}/{f}" for f in includes.get("css", [])]
        js_urls = [f"/themes/{theme_name}/{f}" for f in includes.get("js", [])]
        return css_urls, js_urls

    light_css_urls, light_js_urls = build_urls(light_includes, selection["light"])
    dark_css_urls, dark_js_urls = build_urls(dark_includes, selection["dark"])

    return ThemeStyles(
        css=css,
        font_links=font_links,
        single=selection["single"],
        dark=palette_is_dark(light),
        # New fields
        light_css_urls=light_css_urls,
        light_js_urls=light_js_urls,
        dark_css_urls=dark_css_urls,
        dark_js_urls=dark_js_urls,
    )
```

### Updated `ThemeStyles` NamedTuple

```python
class ThemeStyles(NamedTuple):
    css: str
    font_links: list
    single: bool
    dark: bool
    # New fields
    light_css_urls: list
    light_js_urls: list
    dark_css_urls: list
    dark_js_urls: list
```

## Template Changes (`src/templates/index.html`)

The server cannot know the visitor's light/dark mode — it is chosen in-page from `localStorage`/`prefers-color-scheme` — so include selection happens client-side.

```html
<head>
    <!-- Both themes' CSS includes; only the active mode's stay enabled -->
    {% for url in theme_light_css_urls %}
    <link rel="stylesheet" href="{{ url }}" data-theme-include="light">
    {% endfor %}
    {% if not theme_single %}
    {% for url in theme_dark_css_urls %}
    <link rel="stylesheet" href="{{ url }}" data-theme-include="dark">
    {% endfor %}
    {% endif %}

    <script>
        window.themeIncludes = { js: { light: [...], dark: [...] } };
        // sets data-theme, then disables every <link> whose mode is not active
    </script>
    <style>{{ theme_css }}</style>
    ...
</head>
<body>
    ...
    <!-- Loads only the active mode's ES modules -->
    <script type="module">loadThemeScripts(document.documentElement.dataset.theme)</script>
</body>
```

**Load Order:**
1. Theme CSS variables (inline `<style>`)
2. Theme CSS includes (`<link>`, both modes, active one enabled)
3. Plugin style rules
4. Theme JS includes of the active mode (`<script type="module">`)

In single-theme mode only the light set is emitted (light and dark resolve to the same theme). When a theme declares JS includes, toggling modes reloads the page so the newly active mode's modules run cleanly.

No `window.themeInitConfig`, no `themeInitConfig` global. Theme JS modules are standard ES modules that execute on load.

## Config Integration (`src/main.py`)

No changes needed — `theme_options` removed. Template context only needs theme URLs.

## File Structure Example

```
src/themes/winter/
├── theme.yml
└── static/
    ├── fonts.css
    ├── theme.css
    ├── theme.js
    ├── snowflake.svg
    └── animations/
        └── drift.css
```

```yaml
# theme.yml
name: "Winter"
extends: "default-dark"

includes:
  css:
    - "theme.css"
    - "animations/drift.css"
  js:
    - "theme.js"
```

```css
/* theme.css */
.winter-bg {
    background-image: url("snowflake.svg");
    background-repeat: no-repeat;
    background-position: center top;
}
```

```javascript
// theme.js — standard ES module, runs on load
const canvas = document.createElement('canvas');
// ... snow animation ...
```

## Validation

- Theme loader validates `includes` structure and file existence
- Missing files → `ThemeError` at config load (blocks server start)
- No validation of CSS/JS content

## Testing

- `tests/test_themes.py`: test `includes` parsing, validation, URL generation
- `tests/test_server.py`: verify CSS/JS links in rendered HTML
- `tests/test_template.py`: verify template renders includes correctly

## Migration

- No breaking changes — `includes` is optional
- Existing themes work unchanged
- Documentation updated in `docs/themes.md`