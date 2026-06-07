# Image Plugin Specification

## Purpose

The Image plugin displays a single image in a card, fetched from one of three provider types: RSS, REST, or file. Images are cached server-side with dimensions extracted from file headers to prevent layout shift.

## Requirements

### Requirement: Image plugin displays a single image
The system SHALL display a single image in a card, fetched from one of three provider types: RSS, REST, or file.

#### Scenario: Image displayed with all provider types
- **WHEN** a card has `plugin: image` with `provider_type` set to `rss`, `rest`, or `file`
- **THEN** the image is displayed in the card

### Requirement: RSS provider extracts image from latest feed item
The system SHALL parse the RSS feed using feedparser and extract the image from the latest entry using the following priority: media_thumbnail, media_content (medium=image), enclosure (type=image/*), or `<img>` tag in content/summary HTML.

#### Scenario: Image extracted from media_thumbnail
- **WHEN** the RSS entry has a `media_thumbnail` field
- **THEN** the first thumbnail URL is used as the image

#### Scenario: Image extracted from media_content
- **WHEN** the RSS entry has a `media_content` field with an entry where `medium == "image"`
- **THEN** that entry's URL is used as the image

#### Scenario: Image extracted from enclosure
- **WHEN** the RSS entry has an enclosure with `type` starting with `image/`
- **THEN** the enclosure's URL is used as the image

#### Scenario: Image extracted from content HTML
- **WHEN** none of the above methods yield an image, but the entry's `content` or `summary` contains an `<img>` tag
- **THEN** the first `<img>` tag's `src` attribute is used as the image

#### Scenario: RSS clickable link
- **WHEN** an image is fetched from RSS
- **THEN** the image links to the RSS entry's link URL

### Requirement: REST provider extracts image from API response
The system SHALL fetch the API response and extract the image based on the Content-Type header.

#### Scenario: Response is an image
- **WHEN** the response Content-Type starts with `image/`
- **THEN** the response body is used directly as the image

#### Scenario: Response is JSON with image URL
- **WHEN** the response Content-Type is `application/json`
- **THEN** the system parses the JSON and searches all string values recursively for a URL that looks like an image (contains an image extension or resolves to an image Content-Type)

#### Scenario: Response is XML or HTML with img tag
- **WHEN** the response Content-Type is `text/html`, `text/xml`, or `application/xml`
- **THEN** the system parses the response and finds the first `<img>` tag's `src` attribute

#### Scenario: REST clickable link
- **WHEN** the REST response contains a URL that looks like a page (not an image), that URL is used as the clickable link
- **WHEN** the REST response is a direct image, the `url` option value is used as the clickable link

### Requirement: File provider serves local image
The system SHALL treat the `url` option as a relative path under `/static/custom/` and serve the image from disk.

#### Scenario: File image displayed
- **WHEN** `provider_type` is `file`
- **THEN** the image is read from `/static/custom/<url>` and displayed

#### Scenario: File clickable link
- **WHEN** `provider_type` is `file`
- **THEN** the image links to `#` (no external source)

### Requirement: Image cached server-side
The system SHALL download the image to `cache/image/<card_id>/comic.<ext>` (one file per card). The old image SHALL be deleted before downloading the new one.

#### Scenario: Image cached on fetch
- **WHEN** an image is successfully fetched from any provider
- **THEN** the image is saved to the local cache directory

#### Scenario: Old image deleted on refresh
- **WHEN** a new image is fetched
- **THEN** the previous cached image is deleted before the new one is saved

#### Scenario: Cached image served in template
- **WHEN** the image plugin renders
- **THEN** the image source points to the local cached path

### Requirement: Image dimensions extracted from file headers
The system SHALL extract width and height from PNG/JPEG file headers using `struct.unpack` and store them in the database.

#### Scenario: PNG dimensions extracted
- **WHEN** the cached image is a PNG file
- **THEN** width and height are read from bytes 16-23 of the file

#### Scenario: JPEG dimensions extracted
- **WHEN** the cached image is a JPEG file
- **THEN** width and height are read from the first SOF0 or SOF2 marker

#### Scenario: Dimensions passed to template
- **WHEN** the image plugin renders
- **THEN** the `<img>` tag includes `width` and `height` attributes

### Requirement: Optional schedule
The system SHALL accept an optional `schedule` option (cron expression). If absent, the image SHALL be fetched on every page load. If present, the image SHALL be fetched on setup and on the cron schedule.

#### Scenario: No schedule provided
- **WHEN** `schedule` is not in options
- **THEN** no cron job is registered, and the image is fetched in `render()` if the cache is empty

#### Scenario: Schedule provided
- **WHEN** `schedule` is a valid cron expression
- **THEN** the image is fetched on setup and refreshed on the cron schedule

### Requirement: Optional footer_html
The system SHALL accept an optional `footer_html` option and render it as raw HTML below the image.

#### Scenario: Footer HTML displayed
- **WHEN** `footer_html` is provided
- **THEN** the HTML is rendered below the image

#### Scenario: No footer HTML
- **WHEN** `footer_html` is not provided
- **THEN** nothing is rendered below the image

### Requirement: Config validation
The system SHALL validate that `provider_type` is one of `rss`, `rest`, or `file`, and that `url` is provided.

#### Scenario: Missing provider_type
- **WHEN** `provider_type` is not provided
- **THEN** a ConfigError is raised

#### Scenario: Invalid provider_type
- **WHEN** `provider_type` is not `rss`, `rest`, or `file`
- **THEN** a ConfigError is raised

#### Scenario: Missing url
- **WHEN** `url` is not provided
- **THEN** a ConfigError is raised

### Requirement: Request method for REST
The system SHALL accept an optional `request_method` option for REST provider (default: GET). The system SHALL use this method when fetching the API response.

#### Scenario: GET request (default)
- **WHEN** `request_method` is not provided
- **THEN** a GET request is used

#### Scenario: POST request
- **WHEN** `request_method` is `POST`
- **THEN** a POST request is used
