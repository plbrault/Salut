## 1. Config Schema Update

- [x] 1.1 Update `starter.yaml` to use new schema (`page_title`, `page_header`, `user_info`, `language`)
- [x] 1.2 Update `app/config.py` validation to require `page_title`, `page_header`, `language`, `user_info.short_name`, `user_info.long_name`
- [x] 1.3 Add language validation with BCP 47 support and simple code normalization

## 2. Template Resolver

- [x] 2.1 Create `app/template.py` with `resolve_config_vars()` function for `${...}` syntax
- [x] 2.2 Add tests for template resolver in `tests/test_template.py`

## 3. Integration

- [x] 3.1 Update `app/main.py` to use template resolver from `app/template.py`
- [x] 3.2 Update `app/templates/index.html` to use resolved `page_title` and `page_header`
- [x] 3.3 Add inline JavaScript to replace `{{time_emoji}}` with correct emoji
- [x] 3.4 Set `<html lang>` from language config
- [x] 3.5 Compute and pass localized datetime to template

## 4. Styling

- [x] 4.1 Template owns styling: `<header>` wrapper with Tailwind classes for `h1` and `small`
- [x] 4.2 Config `page_header` contains plain text only (no HTML/styling)

## 5. Documentation

- [x] 5.1 Create `docs/config.md` with YAML config reference
- [x] 5.2 Update `AGENTS.md` with spec-driven workflow documentation

## 6. Tests

- [x] 6.1 Update `tests/test_config.py` for new required fields and language validation
- [x] 6.2 Create `tests/test_template.py` for template resolver
- [x] 6.3 Update `tests/test_server.py` for new template variables and HTML structure

## 7. Specs Update

- [x] 7.1 Sync delta specs to main specs at `openspec/specs/config-loading/spec.md`
