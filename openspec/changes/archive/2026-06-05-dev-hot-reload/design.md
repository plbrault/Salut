## Context

The Salut app uses FastAPI with Jinja2 templates. Currently, `uvicorn.run()` is called with `reload=True` when running directly, but Jinja2's template caching means template changes still require a restart. We need an environment-based dev mode that enables template auto-reload during development while keeping production fast.

## Goals / Non-Goals

**Goals:**
- Add `pipenv run develop` script
- Enable Jinja2 template auto-reload when `DEVELOPMENT` env var is set
- Keep production behavior unchanged (template caching enabled)

**Non-Goals:**
- Auto-reloading Python code changes (uvicorn already handles this)
- Auto-reloading static assets (Tailwind/HTMX)
- Live browser refresh (out of scope for now)

## Decisions

### 1. Environment variable: `DEVELOPMENT`

**Decision:** Use `DEVELOPMENT` environment variable to indicate dev mode.

**Rationale:**
- Environment variables are standard for mode switching
- No config file changes needed
- Easy to set in scripts, CI, or shell

**Alternatives considered:**
- Config file option: Rejected because config files might be committed/shared
- Command-line argument: More complex to thread through uvicorn

### 2. Pipenv script: `pipenv run develop`

**Decision:** Add a `develop` script that starts uvicorn with `DEVELOPMENT=1`.

**Rationale:**
- Simple `pipenv run develop` command
- Consistent with existing `pipenv run app` pattern

**Alternatives considered:**
- Manual env var export: `DEVELOPMENT=1 pipenv run app` — less discoverable

### 3. Jinja2 auto-reload configuration

**Decision:** Check `os.environ.get("DEVELOPMENT")` and set `auto_reload` on the Jinja2 `Environment`.

**Rationale:**
- Jinja2 natively supports `auto_reload` which checks template modification times
- No external dependencies needed
- Simple implementation: just check env var and pass to `Jinja2Templates`

**Alternatives considered:**
- File watching library: Overkill, Jinja2 already handles this
- Template versioning: Complex, unnecessary for development

## Risks / Trade-offs

- **Performance in dev mode**: Jinja2 auto-reload checks file modification times on each request. This is negligible for development but would be undesirable in production → Mitigated by only enabling when `DEVELOPMENT` is set

- **Environment variable persistence**: `DEVELOPMENT` must be set in the shell running the server → Documented in README
