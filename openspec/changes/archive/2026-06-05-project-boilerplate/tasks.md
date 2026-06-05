## 1. Project Setup

- [x] 1.1 Create `Pipfile` with dependencies: fastapi, uvicorn, jinja2, pyyaml, feedparser, apscheduler, pylint, pytest
- [x] 1.2 Create `app/` directory with `__init__.py`
- [x] 1.3 Create `app/templates/` directory
- [x] 1.4 Create `static/` directory for future CSS/images
- [x] 1.5 Create `.gitignore` with `config.yml` entry
- [x] 1.6 Create `.pylintrc` with sensible defaults
- [x] 1.7 Create `pyproject.toml` with pytest configuration

## 2. FastAPI Server

- [x] 2.1 Create `app/main.py` with FastAPI app instance
- [x] 2.2 Configure Jinja2 template renderer in the FastAPI app
- [x] 2.3 Create `GET /` endpoint that renders `index.html` with config context
- [x] 2.4 Add uvicorn entry point in `__main__` block

## 3. SQLite Database

- [x] 3.1 Create `app/database.py` with SQLite initialization function
- [x] 3.2 Create `feed_items` table schema (url, title, link, published, feed_url, fetched_at)
- [x] 3.3 Enable WAL journal mode on connection
- [x] 3.4 Call database initialization on app startup

## 4. YAML Config

- [x] 4.1 Create `app/config.py` with YAML loading function
- [x] 4.2 Load `config.yml` if it exists, otherwise fall back to `starter.yaml`
- [x] 4.3 Validate basic schema (columns array, cards with title and type)
- [x] 4.4 Return structured errors for missing files, parse errors, and validation failures
- [x] 4.5 Call config loading on app startup and pass to template context

## 5. Template

- [x] 5.1 Create `app/templates/index.html` with HTML boilerplate, HTMX script tag, and placeholder for columns/cards
- [x] 5.2 Pass config columns/cards to the template

## 6. Default Config

- [x] 6.1 Create `starter.yaml` with title, one column, and placeholder cards (one of each future type: newsfeed, search, weather, github)

## 7. Tests

- [x] 7.1 Create `tests/` directory with `__init__.py`
- [x] 7.2 Create `tests/test_config.py` — config loading: fallback to config.yml, fallback to starter.yaml, error when both missing, error on invalid YAML, error on missing columns/title/type
- [x] 7.3 Create `tests/test_database.py` — database init: feed_items table exists, WAL mode enabled
- [x] 7.4 Create `tests/test_server.py` — GET / returns 200, response contains expected HTML
- [x] 7.5 Run `pytest` and verify all tests pass
- [x] 7.6 Run `pylint app/ tests/` and verify no errors

## 8. CI

- [x] 8.1 Create `.github/workflows/ci.yml` triggered on pull requests
- [x] 8.2 Workflow installs pipenv and dependencies
- [x] 8.3 Workflow runs `pylint app/ tests/`
- [x] 8.4 Workflow runs `pytest`

## 9. README

- [x] 9.1 Update `README.md` with prerequisites, installation, configuration, running, testing, and linting instructions
