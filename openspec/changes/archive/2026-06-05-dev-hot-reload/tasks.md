## 1. Pipenv Script

- [x] 1.1 Add `develop` script to `Pipfile` that runs uvicorn with `DEVELOPMENT=1`

## 2. Server Configuration

- [x] 2.1 Update `src/main.py` to check `DEVELOPMENT` environment variable
- [x] 2.2 Configure Jinja2 `auto_reload` based on `DEVELOPMENT` flag

## 3. Tests

- [x] 3.1 Add tests for template auto-reload behavior with/without `DEVELOPMENT`

## 4. Documentation

- [x] 4.1 Update `README.md` with `pipenv run develop` usage
