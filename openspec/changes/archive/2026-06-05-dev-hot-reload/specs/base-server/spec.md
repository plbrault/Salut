## MODIFIED Requirements

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
