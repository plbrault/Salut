# Salut — Agent Guidelines

## Project Overview

Salut is a single-user, self-hosted start page with YAML-based configuration. Users customize their page via `config.yml` (or `starter.yml` as default).

## Workflow

This project is **spec-driven**. All features must be specified with OpenSpec before implementation.

1. **Specify** — Create or update a change in `openspec/changes/` using the available skills:
   - `/opsx-propose` — Propose a new change (creates all artifacts in one step)
   - `/opsx-apply` — Implement tasks from an existing change
   - `/opsx-archive` — Archive a completed change
2. **Implement** — Follow the tasks defined in the change's `tasks.md`
3. **Verify** — Run `pipenv run pytest` and `pipenv run pylint`
4. **Sync** — Keep OpenSpec artifacts (proposal, design, specs, tasks) in sync with code changes

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

### Server Testing

Always test the actual server output when making server-side changes:
- Run the server with `PORT=9001 pipenv run develop` (or another port)
- Check both API responses and log output
- Verify the feature works end-to-end in the browser or via curl

### Documentation

**Docs must be kept up-to-date with code changes.** When you add or modify features, update the relevant docs:

- `docs/config.md` — configuration reference
- `docs/plugins/` — plugin documentation
- `README.md` — project overview and links
