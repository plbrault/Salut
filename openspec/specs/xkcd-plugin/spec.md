## Purpose

XKCD plugin for fetching and displaying the latest XKCD comic on the starter page.

## Requirements

### Requirement: XKCD plugin uses Plugin class
The system SHALL provide an `XkcdPlugin` class extending `Plugin` that fetches the latest XKCD comic and renders it.

#### Scenario: XKCD plugin setup fetches comic and schedules refresh
- **WHEN** `XkcdPlugin.setup()` is called with valid options
- **THEN** it fetches the latest comic from the XKCD API, stores it in the database, and registers a cron job with the scheduler

#### Scenario: XKCD plugin renders comic from database
- **WHEN** a card has `plugin: xkcd` with a comic in the database
- **THEN** the rendered card contains the comic image, title, and description

#### Scenario: XKCD plugin owns its database schema
- **WHEN** `XkcdPlugin.init_schema(database)` is called
- **THEN** it creates the `xkcd_comics` table if it does not exist

#### Scenario: XKCD plugin validates options
- **WHEN** `XkcdPlugin.validate_options()` is called
- **THEN** it checks that `schedule` is a valid cron expression

#### Scenario: XKCD plugin renders using template
- **WHEN** `XkcdPlugin.render()` is called
- **THEN** it renders the comic using a Jinja2 template at `src/plugins/xkcd/template.html`

### Requirement: XKCD plugin displays comic with links
The system SHALL display the latest XKCD comic with the comic image, title, and image description (alt text). The comic image SHALL link to the corresponding XKCD page. A separate link SHALL be provided to the "Explain XKCD" page for that comic.

#### Scenario: Comic image links to XKCD page
- **WHEN** the XKCD plugin renders a comic
- **THEN** the comic image is wrapped in a link to `https://xkcd.com/<comic_num>/`

#### Scenario: Explain link points to explain xkcd
- **WHEN** the XKCD plugin renders a comic
- **THEN** a link to `https://www.explainxkcd.com/wiki/index.php/<comic_num>` is displayed

#### Scenario: Comic title and description are displayed
- **WHEN** the XKCD plugin renders a comic
- **THEN** the comic title and alt text (description) are visible in the card

### Requirement: XKCD plugin fetches from JSON API
The system SHALL fetch XKCD comics from `https://xkcd.com/info.0.json` using the `requests` library with a 10-second timeout. On fetch, it SHALL delete the previous comic from the database and cache before storing the new one.

#### Scenario: Successful fetch stores comic data
- **WHEN** the XKCD API returns a valid response
- **THEN** the previous comic is deleted, and the new comic number, title, image URL, and alt text are stored in the database

#### Scenario: Failed fetch logs warning and does not crash
- **WHEN** the XKCD API request fails or returns invalid data
- **THEN** a warning is logged and the plugin continues without crashing

### Requirement: XKCD plugin caches comic image
The system SHALL download the comic image locally using `ImageCache` with an explicit filename (`comic.<ext>`). Only one image SHALL be kept per card — the new image SHALL be downloaded and written before the old database row and old cache file are deleted. Old cache files SHALL be removed via `ImageCache.cleanup_orphans` after the new database row is written. The image dimensions SHALL be extracted from the downloaded file headers and stored in the database.

#### Scenario: Image downloaded on fetch
- **WHEN** a comic is successfully fetched
- **THEN** the comic image is downloaded to the local cache directory via `ImageCache.download`

#### Scenario: Image dimensions extracted from file headers
- **WHEN** a comic image is downloaded
- **THEN** the width and height are extracted from the PNG or JPEG file headers

#### Scenario: Old image deleted after new image is stored
- **WHEN** a new comic is fetched
- **THEN** the previous cached image and database row are deleted only after the new image is downloaded and the new database row is written

#### Scenario: Cached image served in template
- **WHEN** the XKCD plugin renders a comic
- **THEN** the image source points to the local cached path with width and height attributes

#### Scenario: Failed download preserves previous image
- **WHEN** `ImageCache.download` returns `None` and a previous comic exists in the database
- **THEN** the previous database row and cache file are preserved and the old comic continues to be displayed

### Requirement: Each XKCD card gets its own setup
The system SHALL call `setup` for every card with `plugin: xkcd`, even when multiple cards use the same plugin.

#### Scenario: Multiple XKCD cards
- **WHEN** two cards both have `plugin: xkcd`
- **THEN** the system calls `setup` for each card independently, and each card fetches its own comic data
