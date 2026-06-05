## Why

During development, template changes require a server restart to take effect. This slows down the development workflow. We need HTML templates to hot reload when changed in development mode, while keeping production fast with caching.

## What Changes

- Add `pipenv run develop` script that starts the server with a `DEVELOPMENT` environment variable
- Configure Jinja2 template auto-reload when `DEVELOPMENT` is set
- Production script (`pipenv run app`) remains unchanged

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `base-server`: Add environment-based dev mode detection and configure Jinja2 auto-reload

## Impact

- `src/main.py`: Check `DEVELOPMENT` env var, configure Jinja2 `auto_reload`
- `Pipfile`: Add `develop` script
