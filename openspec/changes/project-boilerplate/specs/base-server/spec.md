## ADDED Requirements

### Requirement: FastAPI serves the index page
The server SHALL serve an index page at `GET /` using Jinja2 templates.

#### Scenario: Page loads successfully
- **WHEN** a user navigates to `/`
- **THEN** the server returns a 200 response with HTML content

#### Scenario: Config is passed to template
- **WHEN** the index page is rendered
- **THEN** the Jinja2 template receives the parsed YAML config as context

### Requirement: Static assets are served
The server SHALL serve static files (HTMX, Tailwind CSS) from the `static/` directory.

#### Scenario: HTMX is available locally
- **WHEN** the page loads in a browser
- **THEN** the HTMX library is loaded from `/static/htmx.min.js`

#### Scenario: Tailwind CSS is available locally
- **WHEN** the page loads in a browser
- **THEN** Tailwind CSS is loaded from `/static/tailwindcss.js`

### Requirement: SQLite database is initialized
The server SHALL create and initialize a SQLite database on startup.

#### Scenario: Database file is created
- **WHEN** the server starts for the first time
- **THEN** a SQLite database file exists (e.g., `salut.db`)

#### Scenario: WAL mode is enabled
- **WHEN** the database is initialized
- **THEN** WAL journal mode is active

#### Scenario: Database tables exist
- **WHEN** the database is initialized
- **THEN** the `feed_items` table exists with the correct schema (url, title, link, published, feed_url, fetched_at)
