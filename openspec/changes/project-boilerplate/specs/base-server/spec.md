## ADDED Requirements

### Requirement: FastAPI serves the index page
The server SHALL serve an index page at `GET /` using Jinja2 templates.

#### Scenario: Page loads successfully
- **WHEN** a user navigates to `/`
- **THEN** the server returns a 200 response with HTML content

#### Scenario: Config is passed to template
- **WHEN** the index page is rendered
- **THEN** the Jinja2 template receives the parsed YAML config as context

### Requirement: Template includes HTMX
The HTML template SHALL include the HTMX script tag for dynamic updates.

#### Scenario: HTMX is available
- **WHEN** the page loads in a browser
- **THEN** the HTMX library is loaded and available for use

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
