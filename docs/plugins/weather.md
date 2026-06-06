# Weather Plugin

Fetches and displays current weather conditions from Open-Meteo. Data is cached in the database and refreshed on a cron schedule.

## Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `provider` | string | yes | - | Must be `"open-meteo"` |
| `latitude` | float | yes | - | Geographic latitude (WGS84) |
| `longitude` | float | yes | - | Geographic longitude (WGS84) |
| `location_name` | string | yes | - | Display name for the location (e.g., `"Montréal (Québec)"`) |
| `schedule` | string | yes | - | Cron expression for refresh schedule (e.g., `"0 */2 * * *"`) |
| `units` | string | no | `"celsius"` | Temperature units: `"celsius"` or `"fahrenheit"` |
| `language` | string | no | `"en"` | Language for weather descriptions (passed to Open-Meteo API) |
| `link_url` | string | no | - | URL to open when the card is clicked |

## Example

```yaml
cards:
  - title: Weather
    plugin: weather
    options:
      provider: open-meteo
      latitude: 45.50884
      longitude: -73.58781
      location_name: "Montréal (Québec)"
      schedule: "0 */2 * * *"
      units: celsius
      language: en
```

Weather data is cached in the `weather_data` table and refreshed according to the schedule.
