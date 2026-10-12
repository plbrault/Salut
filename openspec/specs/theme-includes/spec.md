# Spec: Theme Includes

## Purpose

Allows themes to declare CSS and JavaScript files that are automatically loaded into the start page, enabling visual effects like background images, CSS animations, and canvas-based animations without requiring custom plugins.

## Requirements

### Requirement: Theme declares CSS and JS includes in theme.yml
A theme SHALL be able to declare an `includes` section in its `theme.yml` containing `css` (array of file paths) and `js` (array of file paths).

#### Scenario: Valid includes declaration loads files
- **WHEN** a theme has `includes: { css: ["theme.css"], js: ["theme.js"] }` in theme.yml
- **THEN** the theme loader parses the includes without error
- **THEN** the files are verified to exist in the theme's static/ directory

#### Scenario: Missing file in includes raises validation error
- **WHEN** a theme declares a CSS or JS file that does not exist in static/
- **THEN** the theme loader raises a ThemeError with the missing file path
- **THEN** the server fails to start with a clear error message

#### Scenario: Invalid includes structure raises validation error
- **WHEN** includes.css is not a list, or includes.js is not a list
- **THEN** the theme loader raises a ThemeError describing the type mismatch

### Requirement: CSS includes are inlined as style blocks in document head
CSS files declared in includes.css SHALL be inlined as `<style data-theme-include="light|dark">` blocks in the `<head>`, after theme CSS variables and before plugin styles. The block matching the active mode SHALL be enabled and the other disabled.

#### Scenario: Single theme mode inlines light theme includes
- **WHEN** config has `theme: halloween` (single theme mode)
- **THEN** the rendered page contains an inline `<style data-theme-include="light">` block with halloween's theme.css contents in head

#### Scenario: Light/dark mode uses respective theme includes
- **WHEN** config has `theme: { light: halloween, dark: winter }`
- **THEN** the page contains an inline `<style data-theme-include="light">` block with halloween's CSS
- **THEN** the page contains an inline `<style data-theme-include="dark">` block with winter's CSS
- **THEN** only the block matching the active mode is enabled

#### Scenario: CSS load order is preserved
- **WHEN** includes.css has `["theme.css", "animations/float.css"]`
- **THEN** the contents of theme.css appear before animations/float.css in the head

### Requirement: JS includes are injected as ES modules at end of body
JavaScript files declared in includes.js SHALL be injected as `<script type="module">` elements at the end of `<body>`, after all page content.

#### Scenario: JS modules load in declared order
- **WHEN** includes.js has `["theme.js", "lib/particles.js"]`
- **THEN** the script for theme.js appears before lib/particles.js in the body

#### Scenario: JS files served from theme static directory
- **WHEN** theme.js is requested at `/themes/halloween/theme.js`
- **THEN** the file is served from src/themes/halloween/static/theme.js with correct MIME type

### Requirement: Theme inheritance behavior
Child themes SHALL NOT inherit parent's includes. Each theme must explicitly declare its own `includes` to have custom CSS/JS files loaded.

#### Scenario: Child theme with includes uses its own
- **WHEN** parent theme has includes.css = ["base.css"] and child theme has includes.css = ["theme.css"]
- **THEN** only theme.css is loaded (not base.css)

#### Scenario: Child theme without includes loads no extra CSS/JS
- **WHEN** parent theme has includes.css = ["base.css"] and child theme omits includes entirely
- **THEN** no CSS/JS includes are loaded for the child theme

### Requirement: Relative asset paths in theme CSS resolve correctly
CSS files in theme static/ SHALL be able to reference sibling assets (images, fonts) using relative URLs. Because theme CSS is inlined into the page, the server SHALL rewrite bare relative `url(...)` references to absolute `/themes/<name>/...` paths at render time.

#### Scenario: Background image in theme.css uses relative path
- **WHEN** theme.css contains `background-image: url("pumpkin.svg")`
- **THEN** the inlined CSS contains `url("/themes/halloween/pumpkin.svg")`
- **THEN** the image loads successfully

### Requirement: No themeInitConfig global is injected
- **WHEN** a theme with includes.js is active
- **THEN** NO `window.themeInitConfig` global is present in the rendered HTML
- **THEN** theme JS modules are standard ES modules that execute on load