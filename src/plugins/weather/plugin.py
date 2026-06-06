import hashlib
import json
from pathlib import Path

import requests

from src.config import ConfigError
from src.plugin import Plugin

WMO_ICONS = {
    0: ("☀️", "Clear sky"),
    1: ("🌤️", "Mainly clear"),
    2: ("⛅", "Partly cloudy"),
    3: ("☁️", "Overcast"),
    45: ("🌫️", "Fog"),
    48: ("🌫️", "Depositing rime fog"),
    51: ("🌦️", "Light drizzle"),
    53: ("🌦️", "Moderate drizzle"),
    55: ("🌦️", "Dense drizzle"),
    56: ("🌧️", "Light freezing drizzle"),
    57: ("🌧️", "Dense freezing drizzle"),
    61: ("🌧️", "Slight rain"),
    63: ("🌧️", "Moderate rain"),
    65: ("🌧️", "Heavy rain"),
    66: ("🌧️", "Light freezing rain"),
    67: ("🌧️", "Heavy freezing rain"),
    71: ("❄️", "Slight snow"),
    73: ("❄️", "Moderate snow"),
    75: ("❄️", "Heavy snow"),
    77: ("❄️", "Snow grains"),
    80: ("🌧️", "Slight rain showers"),
    81: ("🌧️", "Moderate rain showers"),
    82: ("🌧️", "Violent rain showers"),
    85: ("🌨️", "Slight snow showers"),
    86: ("🌨️", "Heavy snow showers"),
    95: ("⛈️", "Thunderstorm"),
    96: ("⛈️", "Thunderstorm with slight hail"),
    99: ("⛈️", "Thunderstorm with heavy hail"),
}


class WeatherPlugin(Plugin):
    def __init__(self):
        self._database = None
        self._logger = None
        self._card_id = None
        self._template = self.load_template(
            Path(__file__).resolve().parent, "template.html"
        )

    @staticmethod
    def validate_options(options, card_idx, filename):
        if not options:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options is required for weather plugin."
            )

        provider = options.get("provider")
        if not provider:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.provider is required."
            )
        if provider != "open-meteo":
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.provider must be 'open-meteo'."
            )

        latitude = options.get("latitude")
        if latitude is None or not isinstance(latitude, (int, float)):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.latitude is required and must be a number."
            )

        longitude = options.get("longitude")
        if longitude is None or not isinstance(longitude, (int, float)):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.longitude is required and must be a number."
            )

        location_name = options.get("location_name")
        if not location_name or not isinstance(location_name, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.location_name is required and must be a string."
            )

        schedule = options.get("schedule")
        if not schedule:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.schedule is required (cron expression)."
            )
        if not isinstance(schedule, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.schedule must be a string."
            )
        parts = schedule.strip().split()
        if len(parts) not in (5, 6):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.schedule must be a valid cron expression (5 or 6 fields)."
            )

        units = options.get("units", "celsius")
        if units not in ("celsius", "fahrenheit"):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.units must be 'celsius' or 'fahrenheit'."
            )

        link_url = options.get("link_url")
        if link_url is not None and not isinstance(link_url, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.link_url must be a string."
            )

        provider_link_prefix = options.get("provider_link_prefix")
        if provider_link_prefix is not None and not isinstance(provider_link_prefix, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.provider_link_prefix must be a string."
            )

    @staticmethod
    def init_schema(database):
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL DEFAULT '',
                data TEXT NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def setup(self, options, database, scheduler, logger):
        self._database = database
        self._logger = logger
        self._card_id = self._compute_card_id(options)

        latitude = options["latitude"]
        longitude = options["longitude"]
        units = options.get("units", "celsius")
        language = options.get("language", "en")
        schedule = options["schedule"]

        self._fetch_weather(latitude, longitude, units, language)
        scheduler.add_job(
            self._fetch_weather,
            trigger=self.parse_schedule(schedule),
            args=[latitude, longitude, units, language],
            id=f"weather_{self._card_id}",
            replace_existing=True,
        )

    def render(self, options):
        card_id = self._compute_card_id(options)
        row = self._database.fetch_one(
            "SELECT data FROM weather_data WHERE card_id = ?",
            (card_id,),
        )
        if not row:
            return '<p style="color: var(--text-muted)">Weather data unavailable.</p>'

        data = json.loads(row["data"])
        current = data.get("current", {})
        weather_code = current.get("weather_code", 0)
        is_day = current.get("is_day", 1)
        icon, description = WMO_ICONS.get(weather_code, ("🌡️", "Unknown"))
        if weather_code == 0:
            icon = "☀️" if is_day else "🌙"

        temp_unit = "°C" if options.get("units", "celsius") == "celsius" else "°F"
        provider_prefix = options.get("provider_link_prefix", "Provided by")
        html = self._template.render(
            location_name=options.get("location_name", ""),
            icon=icon,
            description=description,
            temp=current.get("temperature_2m"),
            feels_like=current.get("apparent_temperature"),
            humidity=current.get("relative_humidity_2m"),
            wind=current.get("wind_speed_10m"),
            temp_unit=temp_unit,
            provider_prefix=provider_prefix,
        )

        link_url = options.get("link_url")
        if link_url:
            return (
                f'<a href="{link_url}" target="_blank" rel="noopener"'
                f' class="block text-inherit no-underline">{html}</a>'
            )
        return html

    def _fetch_weather(self, latitude, longitude, units, language):
        try:
            self._logger.info("Fetching weather for %s, %s", latitude, longitude)
            temp_unit = "fahrenheit" if units == "fahrenheit" else "celsius"
            current_fields = (
                "temperature_2m,relative_humidity_2m,"
                "apparent_temperature,weather_code,"
                "wind_speed_10m,is_day"
            )
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": current_fields,
                    "temperature_unit": temp_unit,
                    "language": language,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            self._database.execute(
                "DELETE FROM weather_data WHERE card_id = ?",
                (self._card_id,),
            )
            self._database.execute(
                "INSERT INTO weather_data (card_id, data) VALUES (?, ?)",
                (self._card_id, json.dumps(data)),
            )
            self._logger.info("Weather fetched and cached for card %s", self._card_id)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch weather: %s", e)

    @staticmethod
    def _compute_card_id(options):
        raw = json.dumps(options, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def card_style_rules() -> dict[str, str]:
        return {
            "": "text-align: center;",
            ".weather-body": (
                "display: flex; flex-wrap: wrap; gap: 0.5rem;"
                " justify-content: space-between; align-items: flex-start;"
                " max-width: 80%; margin: 0 auto;"
                "padding-top: 0.5rem;"
            ),
            ".weather-current": "display: flex; justify-content: center;",
            ".weather-icon": "font-size: 3rem; line-height: 1;",
            ".weather-temp": "font-size: 2rem; font-weight: bold; line-height: 1;",
            ".weather-details": (
                "display: flex; flex-direction: column; gap: 0.25rem;"
                " align-items: center;"
            ),
            ".weather-detail": "font-size: 0.875rem; color: var(--text-muted);",
            ".weather-provider": (
                "width: 100%; margin-top: 0.75rem;"
                " font-size: 0.75rem; color: var(--text-faint);"
            ),
            ".weather-provider a": "color: var(--text-faint); text-decoration: none;",
            ".weather-provider a:hover": "text-decoration: underline;",
        }
