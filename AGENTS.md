# Salut — Agent Guidelines

## Project Overview

Salut is a single-user, self-hosted starter page with YAML-based configuration. Users customize their page via `config.yml` (or `starter.yaml` as default).

## Tech Stack

- Python 3.14 + FastAPI
- Jinja2 templating
- HTMX (client-side interactivity)
- Tailwind CSS (styling)
- PyYAML (config loading)
- SQLite (feed item persistence)
- pytest (testing)
- pylint (linting)

## Key Conventions

### Testing

**Tests must be added with every implementation change.** When you implement a feature, fix a bug, or modify behavior, you MUST add or update tests to cover the change.

- Test files live in `tests/`
- Run `pipenv run pytest` before committing
- All tests must pass (0 failures)

### Linting

- Run `pipenv run pylint` before committing
- Maintain a score of 10/10

### Configuration

- Config files use snake_case YAML
- Template variables:
  - `${...}` — references config values (resolved server-side)
  - `{{...}}` — client-side dynamic values (replaced by JavaScript)

### Code Style

- No comments unless the solution is unusual
- Follow existing patterns in the codebase
- Keep functions small and focused
