## 1. Plugin Architecture

- [x] 1.1 Create `src/plugins/__init__.py` with plugin loading logic
- [x] 1.2 Create `src/plugins/html/__init__.py` with `render(options)` function

## 2. Config Updates

- [x] 2.1 Update `starter.yml` to flat cards structure with numeric `columns`
- [x] 2.2 Update `src/config.py` validation for new schema (columns=int, cards=flat list)

## 3. Template Updates

- [x] 3.1 Update `src/main.py` — auto-flow grid layout algorithm
- [x] 3.2 Update `src/templates/index.html` to render plugin content with colspan support

## 4. Tests

- [x] 4.1 Add tests for plugin loading and rendering
- [x] 4.2 Add tests for HTML plugin
- [x] 4.3 Add tests for colspan behavior
- [x] 4.4 Update config validation tests for new schema

## 5. Documentation

- [ ] 5.1 Update `docs/config.md` with new card schema
