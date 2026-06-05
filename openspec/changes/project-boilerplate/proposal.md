## Why

We need a project skeleton to build on. This change sets up the foundation so subsequent changes can focus on individual features.

## What Changes

- Initialize Python project with dependencies (FastAPI, Jinja2, HTMX, PyYAML, APScheduler, feedparser, sqlite3)
- Configure pylint for linting and pytest for testing
- Add GitHub Actions workflow to run lint and tests on pull requests
- Create project directory structure
- Create a minimal FastAPI server that loads a YAML config and renders a basic page
- Server uses `config.yml` if present, otherwise falls back to `starter.yaml` (default config)
- `config.yml` is gitignored so user customizations stay local
- Set up Jinja2 templates with HTMX
- Initialize SQLite database with WAL mode
- Create a sample `starter.yaml` with placeholder card definitions

## Capabilities

### New Capabilities
- `project-setup`: Python project structure, dependencies, entry point, linting, and testing
- `config-loading`: YAML config loading and basic validation
- `base-server`: FastAPI server with Jinja2 rendering and SQLite initialization

### Modified Capabilities
<!-- None — this is a fresh project -->

## Impact

- New Python project using pipenv for dependency management
- FastAPI, Jinja2, PyYAML, APScheduler, feedparser as dependencies
- `.gitignore` to exclude `config.yml`
- `.github/workflows/` for CI pipeline
- SQLite database file created at startup
- No existing code affected — project is at inception
