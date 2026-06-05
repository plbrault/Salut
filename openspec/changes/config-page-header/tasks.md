## 1. Config Schema Update

- [x] 1.1 Update `starter.yaml` to use new schema (`page_title`, `page_header`, `user_info`)
- [x] 1.2 Update `app/config.py` validation to require `page_title`, `page_header`, `user_info.short_name`, `user_info.long_name`
- [x] 1.3 Add tests for new validation rules in `tests/test_config.py`

## 2. Template Resolver

- [x] 2.1 Create `app/template.py` with `resolve_config_vars()` function for `${...}` syntax
- [x] 2.2 Add tests for template resolver in `tests/test_template.py`

## 3. Integration

- [x] 3.1 Update `app/main.py` to use template resolver from `app/template.py`
- [x] 3.2 Update `app/templates/index.html` to use resolved `page_title` and `page_header`
- [x] 3.3 Add inline JavaScript to replace `{{time_emoji}}` with correct emoji
- [x] 3.4 Add tests for server routes in `tests/test_server.py`

## 4. Specs Update

- [x] 4.1 Sync delta specs to main specs at `openspec/specs/config-loading/spec.md`
