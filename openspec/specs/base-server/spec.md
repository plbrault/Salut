## Purpose

FastAPI server with Jinja2 templating, HTMX, Tailwind CSS, and SQLite database initialization.

## Requirements

### Requirement: FastAPI serves the index page
The server SHALL serve an index page at `GET /` using Jinja2 templates.

#### Scenario: Page loads successfully
- **WHEN** a user navigates to `/`
- **THEN** the server returns a 200 response with HTML content

#### Scenario: Config is passed to template
- **WHEN** the index page is rendered
- **THEN** the Jinja2 template receives the parsed YAML config as context

#### Scenario: Template auto-reload in dev mode
- **WHEN** the `DEVELOPMENT` environment variable is set
- **THEN** Jinja2 templates auto-reload when files change (no restart required)

#### Scenario: Template caching in production
- **WHEN** the `DEVELOPMENT` environment variable is not set
- **THEN** Jinja2 templates are cached for performance

### Requirement: Static assets are served
The server SHALL serve static files (HTMX, Tailwind CSS) from the `static/` directory.

#### Scenario: HTMX is available locally
- **WHEN** the page loads in a browser
- **THEN** the HTMX library is loaded from `/static/htmx.min.js`

#### Scenario: Tailwind CSS is available locally
- **WHEN** the page loads in a browser
- **THEN** Tailwind CSS is loaded from `/static/tailwindcss.js`

### Requirement: SQLite database is initialized
The server SHALL delete and recreate the SQLite database on every startup, ensuring a clean state with no persisted data. The scheduler SHALL be configured with `misfire_grace_time=None` so that scheduled jobs are never silently skipped due to timing delays.

#### Scenario: Database is reset on startup
- **WHEN** the server starts
- **THEN** any existing database file is deleted and a fresh database is created

#### Scenario: WAL mode is enabled
- **WHEN** the database is initialized
- **THEN** WAL journal mode is active

#### Scenario: Database tables exist
- **WHEN** the database is initialized
- **THEN** all plugin tables exist with the correct schema (created by `init_plugins_schemas()`)

#### Scenario: Previous data is discarded
- **WHEN** the server restarts with an existing database containing cached data
- **THEN** the cached data is no longer available after restart

#### Scenario: Scheduler never skips misfired jobs
- **WHEN** a scheduled job's fire time is missed due to scheduler thread delay
- **THEN** the job SHALL still execute when the scheduler thread becomes available

#### Scenario: Scheduler misfire grace time is unlimited
- **WHEN** the BackgroundScheduler is initialized
- **THEN** `job_defaults['misfire_grace_time']` SHALL be `None`
