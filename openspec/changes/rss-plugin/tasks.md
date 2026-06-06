## 1. Database Updates

- [x] 1.1 Add `card_id` and `image_url` columns to `feed_items` table in `src/database.py`
- [x] 1.2 Add cleanup function to delete items by card_id

## 2. Plugin Base Class

- [x] 2.1 Create `src/plugins/base.py` with abstract `Plugin` class (setup, render)
- [x] 2.2 Update `src/plugins/__init__.py` to load plugin classes and provide `setup_card`/`render_card`

## 3. HTML Plugin Refactor

- [x] 3.1 Create `src/plugins/html/plugin.py` with `HtmlPlugin(Plugin)` class
- [x] 3.2 Update `src/plugins/html/__init__.py` to re-export `HtmlPlugin`

## 4. RSS Plugin Refactor

- [x] 4.1 Create `src/plugins/rss/plugin.py` with `RssPlugin(Plugin)` class
- [x] 4.2 Move feed fetching, image caching, scheduling logic into `RssPlugin`
- [x] 4.3 Update `src/plugins/rss/__init__.py` to re-export `RssPlugin`

## 5. Main Plugin-Agnostic

- [x] 5.1 Remove all RSS-specific imports and logic from `src/main.py`
- [x] 5.2 Use generic `setup_card`/`render_card` from `src/plugins/__init__.py`
- [x] 5.3 Add logging setup for plugin loggers

## 6. Config Validation

- [x] 6.1 Add RSS card validation (feeds required, refresh required, valid cron)
- [x] 6.2 Update `src/config.py` validation for RSS-specific fields

## 7. Template Updates

- [x] 7.1 Update `src/templates/index.html` to render RSS item list

## 8. Tests

- [x] 8.1 Update plugin tests for new class-based interface
- [x] 8.2 Add tests for plugin loading and instantiation
- [x] 8.3 Verify all existing tests pass

## 9. Documentation

- [x] 9.1 Update `docs/plugins/index.md` with RSS plugin documentation
- [x] 9.2 Update `docs/config.md` with RSS card schema
- [x] 9.3 Add `cache/` to `.gitignore`

## 10. Example Config

- [x] 10.1 Add example RSS cards to `starter.yml`
