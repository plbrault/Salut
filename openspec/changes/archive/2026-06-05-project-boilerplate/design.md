## Context

This is the first implementation change for the Salut project. This change focuses on the minimal viable skeleton: project structure, dependencies, config loading, and a server that renders a basic page.

## Goals / Non-Goals

**Goals:**
- Python project with all required dependencies installed
- Pylint configured for linting
- Pytest configured for testing
- FastAPI server that starts and serves a page
- Jinja2 templates with HTMX and Tailwind CSS wired up
- YAML config loading with basic validation
- SQLite database initialized with WAL mode
- Sample `starter.yaml` with placeholder cards

**Non-Goals:**
- Actual card rendering logic (next change)
- RSS fetching or APScheduler cron jobs (next change)
- Weather, GitHub, or search API integration (next change)
- Styling beyond basic layout

## Decisions

### Project structure
```
salut/
  app/
    __init__.py
    main.py          # FastAPI app, routes
    config.py        # YAML loading and validation
    database.py      # SQLite setup
    templates/
      index.html     # Single page template with HTMX
  static/
    htmx.min.js      # HTMX (v2.0.4, hosted locally)
    tailwindcss.js   # Tailwind CSS play CDN (hosted locally)
  starter.yaml       # Default config (checked into git)
  config.yml         # User config (gitignored, overrides starter.yaml)
  Pipfile            # Dependencies
  Pipfile.lock       # Locked versions
  .pylintrc          # Pylint configuration
  pyproject.toml     # Pytest configuration
  .github/
    workflows/
      ci.yml         # Lint and test on pull requests
```

### Dependencies
- `fastapi` + `uvicorn` — web server
- `jinja2` — templating (comes with FastAPI but pin explicitly)
- `pyyaml` — config parsing
- `feedparser` — installed now, used in next change
- `apscheduler` — installed now, used in next change
- `pylint` — linting (dev dependency)
- `pytest` — testing (dev dependency)

### Static assets: HTMX and Tailwind hosted locally
HTMX and Tailwind CSS are downloaded to `static/` and served by FastAPI's `StaticFiles` middleware. No CDN dependencies — everything works offline and avoids external requests in production.

**Alternative considered**: CDN for both. Rejected — adds external dependency, fails offline, and leaks usage data.

### Config loading: fallback pattern
Check for `config.yml` first. If it exists, use it. Otherwise, fall back to `starter.yaml`. This lets users customize their config without modifying the tracked default. `config.yml` is gitignored.

### Config validation: basic schema check
Validate that the loaded config has `columns` array with `cards`, each card has `title` and `type`. Full type-specific validation comes in subsequent changes.

### SQLite: WAL mode
Enable WAL mode on startup for safe concurrent access when APScheduler runs background fetches later.

## Risks / Trade-offs

- **Dependencies installed but unused** → feedparser and apscheduler are in requirements but not used yet. Acceptable — avoids changing dependencies when adding card features.
- **Placeholder cards** → The sample config will have card definitions that don't render anything useful yet. This is expected — the next change wires up rendering.
