# Tasks: Theme Visual Effects

## Task 1: Update theme vocabulary and validation

- [x] Add `includes` parsing to `load_theme()` in `src/themes/__init__.py`
  - Validate `includes` is a dict with optional `css` (list), `js` (list)
  - Validate all listed files exist in theme's `static/` directory
  - Store `includes` in returned theme data
- [x] Update `resolve_theme()` to NOT inherit parent's `includes` (child themes must declare their own)
- [x] Update `generate_theme_css()` to return `ThemeStyles` with new fields:
  - `light_css_urls`, `light_js_urls`, `dark_css_urls`, `dark_js_urls`
- [x] Update `ThemeStyles` NamedTuple with new fields
- [x] Update `built_in_theme_styles()` to include empty lists for new fields

## Task 2: Update template to inject theme CSS/JS

- [x] In `src/templates/index.html`:
  - Add `theme_light_css_urls`, `theme_dark_css_urls`, `theme_light_js_urls`, `theme_dark_js_urls` to template context
  - In `<head>`: inject `<link rel="stylesheet">` for CSS includes (after theme variables, before plugin styles)
  - At end of `<body>`: inject `<script type="module">` for JS includes
  - Handle both single-theme and light/dark theme modes correctly

## Task 3: Remove theme_options and themeInitConfig from main.py

- [x] In `src/main.py` `index()`:
  - Remove `theme_options` extraction
  - Remove `themeInitConfig` from template context

## Task 4: Clean up template

- [x] In `src/templates/index.html`:
  - Remove `window.themeInitConfig` global
  - Remove `theme_options` from template context
  - Keep CSS/JS include injection only

## Task 5: Add tests

- [x] In `tests/test_themes.py`:
  - Test `includes` parsing with valid CSS/JS arrays
  - Test `includes` validation rejects non-list values
  - Test `includes` validation rejects missing files
  - Test `generate_theme_css()` returns correct URLs for light/dark themes
  - Test inheritance: child theme's `includes` replaces parent's
  - Test `built_in_theme_styles()` includes empty lists for new fields
- [x] In `tests/test_server.py`:
  - Test main page includes theme CSS/JS links when theme has `includes`
  - Test `window.themeInitConfig` is NOT present in rendered HTML
  - Test admin page works without theme descriptions

## Task 6: Update documentation

- [x] Update `docs/themes.md`:
  - Document `includes` section with css/js only
  - Document file structure (static/ folder)
  - Remove `theme_options` documentation
  - Remove `theme.js` contract documentation (init, meta, reducedMotion)

## Task 7: Verification

- [x] Run `pipenv run pytest` — all tests pass
- [x] Run `pipenv run pylint` — score 10/10
- [x] Start server (`PORT=9001 pipenv run develop`), verify in browser:
  - Theme with `includes` loads CSS (check Network tab)
  - Theme with `includes` loads JS modules (check Network tab)
  - NO `window.themeInitConfig` present in console
  - Theme JS runs on load (standard ES module)
  - Light/dark mode switch loads correct theme's includes
  - Custom theme in config.yml works
- [x] Test error handling: missing file in `includes` → clear error on config load

## Task 8: Create draft PR

- [x] Commit all changes with clear commit messages
- [ ] Push branch to origin
- [ ] Create draft PR on GitHub with:
  - Title: "Add theme visual effects (CSS/JS includes)"
  - Description linking to this change: `openspec/changes/theme-visual-effects/`
  - Summary of changes: theme.yml includes, template injection
  - Test plan referencing Task 7 verification steps