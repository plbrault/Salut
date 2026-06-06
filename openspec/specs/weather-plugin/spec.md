## Purpose

Weather plugin that fetches and displays current weather conditions from Open-Meteo, with caching and scheduled refresh.

## Requirements

### Requirement: Weather plugin fetches current conditions
The system SHALL provide a `weather` plugin that fetches current weather conditions from the Open-Meteo API and caches the result in the database.

#### Scenario: Successful weather fetch
- **WHEN** a card has `plugin: weather` with valid options
- **THEN** the system fetches current weather from `https://api.open-meteo.com/v1/forecast` and stores the result in the database

#### Scenario: Weather data served from cache
- **WHEN** a card is rendered and cached weather data exists in the database
- **THEN** the system displays the cached data without making an API call

#### Scenario: Weather fetch failure
- **WHEN** the Open-Meteo API returns an error or is unreachable
- **THEN** the card displays an error message instead of crashing

### Requirement: Weather plugin scheduled refresh
The system SHALL refresh weather data on a cron schedule defined by the `schedule` option, using the same scheduling mechanism as the RSS plugin.

#### Scenario: Scheduled refresh
- **WHEN** a weather card has `schedule: "0 */2 * * *"`
- **THEN** the plugin registers a cron job that fetches fresh weather data every 2 hours

#### Scenario: Card ID from options hash
- **WHEN** a weather card is set up
- **THEN** the plugin computes a unique card ID by hashing its options (like the RSS plugin)

### Requirement: Weather plugin options
The system SHALL accept the following options for weather cards:

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `provider` | string | yes | - | Must be `"open-meteo"` |
| `latitude` | float | yes | - | Geographic latitude (WGS84) |
| `longitude` | float | yes | - | Geographic longitude (WGS84) |
| `location_name` | string | yes | - | Display name for the location (e.g., `"Montréal (Québec)"`) |
| `schedule` | string | yes | - | Cron expression for refresh schedule (e.g., `"0 */2 * * *"`) |
| `units` | string | no | `"celsius"` | Temperature units: `"celsius"` or `"fahrenheit"` |
| `language` | string | no | `"en"` | Language for weather descriptions |
| `link_url` | string | no | - | URL to open when the card is clicked |
| `provider_link_prefix` | string | no | `"Provided by"` | Text before the provider link (for translation) |

#### Scenario: Valid config
- **WHEN** a card has `plugin: weather` with `provider: open-meteo`, `latitude`, `longitude`, `location_name`, and `schedule`
- **THEN** config validation passes

#### Scenario: Missing provider
- **WHEN** a weather card has no `provider` option
- **THEN** a configuration error is raised

#### Scenario: Unsupported provider
- **WHEN** a weather card has a `provider` that is not `"open-meteo"`
- **THEN** a configuration error is raised

#### Scenario: Missing latitude
- **WHEN** a weather card has no `latitude` option
- **THEN** a configuration error is raised

#### Scenario: Missing longitude
- **WHEN** a weather card has no `longitude` option
- **THEN** a configuration error is raised

#### Scenario: Missing location_name
- **WHEN** a weather card has no `location_name` option
- **THEN** a configuration error is raised

#### Scenario: Missing schedule
- **WHEN** a weather card has no `schedule` option
- **THEN** a configuration error is raised

#### Scenario: Invalid schedule format
- **WHEN** a weather card has `schedule` that is not a valid cron expression (5 or 6 fields)
- **THEN** a configuration error is raised

#### Scenario: Invalid units
- **WHEN** a weather card has `units` that is not `"celsius"` or `"fahrenheit"`
- **THEN** a configuration error is raised

#### Scenario: Invalid link_url type
- **WHEN** a weather card has `link_url` that is not a string
- **THEN** a configuration error is raised

#### Scenario: Invalid provider_link_prefix type
- **WHEN** a weather card has `provider_link_prefix` that is not a string
- **THEN** a configuration error is raised

### Requirement: Weather card link
The weather card SHALL be wrapped in an anchor tag when `link_url` is provided, making the entire card clickable.

#### Scenario: Card with link_url
- **WHEN** a weather card has `link_url` set to `"https://example.com/weather"`
- **THEN** the rendered card is wrapped in an `<a>` tag with `href` set to the URL and `target="_blank"`

#### Scenario: Card without link_url
- **WHEN** a weather card has no `link_url` option
- **THEN** the card is rendered as a plain `<div>` without a link wrapper

### Requirement: Weather card displays current conditions
The weather card SHALL display the following information: location name, temperature, feels-like temperature, weather condition with icon, wind speed, and humidity.

#### Scenario: Location displayed
- **WHEN** a weather card has `location_name: "Montréal (Québec)"`
- **THEN** the card displays the location name as a heading or label

#### Scenario: Daytime clear sky
- **WHEN** the current weather code is 0 and `is_day` is 1
- **THEN** the card shows a sun icon (☀️) with "Clear sky"

#### Scenario: Nighttime clear sky
- **WHEN** the current weather code is 0 and `is_day` is 0
- **THEN** the card shows a moon icon (🌙) with "Clear sky"

#### Scenario: Partly cloudy
- **WHEN** the current weather code is 1, 2, or 3
- **THEN** the card shows a cloud icon (⛅ or ☁️) with appropriate description

#### Scenario: Rain
- **WHEN** the current weather code indicates rain (51-67, 80-82)
- **THEN** the card shows a rain icon (🌧️) with "Drizzle", "Rain", or "Heavy rain" as appropriate

#### Scenario: Snow
- **WHEN** the current weather code indicates snow (71-77, 85-86)
- **THEN** the card shows a snow icon (❄️) with "Snow" or related description

#### Scenario: Thunderstorm
- **WHEN** the current weather code indicates thunderstorm (95-99)
- **THEN** the card shows a thunderstorm icon (⛈️) with "Thunderstorm"

### Requirement: Weather card styling
The weather plugin SHALL implement `card_style_rules` with styling appropriate for a weather card.

#### Scenario: Weather card has custom styles
- **WHEN** the weather plugin's `card_style_rules` is queried
- **THEN** it returns a dict with rules for the weather card layout (temperature display, icon sizing, etc.)

### Requirement: Weather card provider attribution
The weather card SHALL display a provider attribution link at the bottom of the card, linking to `https://open-meteo.com/`. The text format is `"{prefix} Open-Meteo"`, where `{prefix}` defaults to `"Provided by"` and is overridable via the `provider_link_prefix` option.

#### Scenario: Default attribution text
- **WHEN** a weather card has no `provider_link_prefix` option
- **THEN** the card displays "Provided by Open-Meteo" with a link to open-meteo.com

#### Scenario: Custom attribution prefix
- **WHEN** a weather card has `provider_link_prefix: "Données de"`
- **THEN** the card displays "Données de Open-Meteo" with a link to open-meteo.com
