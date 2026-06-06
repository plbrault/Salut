import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import caldav

from src.config import ConfigError
from src.plugin import Plugin


class CalendarPlugin(Plugin):
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
                f"{filename}: cards[{card_idx}].options is required for calendar plugin."
            )

        calendars = options.get("calendars")
        if not calendars or not isinstance(calendars, list) or len(calendars) == 0:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.calendars must be a non-empty list."
            )

        for cal_idx, cal in enumerate(calendars):
            CalendarPlugin._validate_calendar_entry(cal, cal_idx, card_idx, filename)

        schedule = options.get("schedule")
        if not schedule or not isinstance(schedule, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.schedule is required (cron expression)."
            )
        parts = schedule.strip().split()
        if len(parts) not in (5, 6):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.schedule must be a valid cron expression (5 or 6 fields)."
            )

        time_window_days = options.get("time_window_days")
        if time_window_days is not None:
            if not isinstance(time_window_days, int) or time_window_days < 1:
                raise ConfigError(
                    f"{filename}: cards[{card_idx}].options.time_window_days must be a positive integer."
                )

        max_events = options.get("max_events")
        if max_events is not None:
            if not isinstance(max_events, int) or max_events < 1:
                raise ConfigError(
                    f"{filename}: cards[{card_idx}].options.max_events must be a positive integer."
                )

        link_url = options.get("link_url")
        if link_url is not None and not isinstance(link_url, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.link_url must be a string."
            )

    @staticmethod
    def _validate_calendar_entry(cal, cal_idx, card_idx, filename):
        prefix = f"{filename}: cards[{card_idx}].options.calendars[{cal_idx}]"
        if not isinstance(cal, dict):
            raise ConfigError(f"{prefix} must be a mapping.")
        if not cal.get("url"):
            raise ConfigError(f"{prefix}.url is required.")
        auth_type = cal.get("auth_type", "basic")
        if auth_type not in ("basic", "bearer"):
            raise ConfigError(f"{prefix}.auth_type must be 'basic' or 'bearer'.")
        if auth_type == "bearer" and not cal.get("bearer_token"):
            raise ConfigError(
                f"{prefix}.bearer_token is required when auth_type is 'bearer'."
            )

    @staticmethod
    def init_schema(database):
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL DEFAULT '',
                events TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def setup(self, options, database, scheduler, logger):
        self._database = database
        self._logger = logger
        self._card_id = self._compute_card_id(options)

        calendars = options.get("calendars", [])
        time_window_days = options.get("time_window_days", 7)
        schedule = options["schedule"]

        self._fetch_events(calendars, time_window_days)
        scheduler.add_job(
            self._fetch_events,
            trigger=self.parse_schedule(schedule),
            args=[calendars, time_window_days],
            id=f"calendar_{self._card_id}",
            replace_existing=True,
        )

    def render(self, options):
        card_id = self._compute_card_id(options)
        row = self._database.fetch_one(
            "SELECT events FROM calendar_events WHERE card_id = ?",
            (card_id,),
        )
        if not row:
            return '<p style="color: var(--text-muted)">No upcoming events.</p>'

        events = json.loads(row["events"])
        max_events = options.get("max_events", 10)

        events.sort(key=lambda e: e.get("start", ""))
        events = events[:max_events]

        if not events:
            return '<p style="color: var(--text-muted)">No upcoming events.</p>'

        html = self._template.render(events=events)

        link_url = options.get("link_url")
        if link_url:
            return (
                f'<a href="{link_url}" target="_blank" rel="noopener"'
                f' class="block text-inherit no-underline">{html}</a>'
            )
        return html

    def _fetch_events(self, calendars, time_window_days):
        self._logger.info(
            "Fetching calendar events for card %s (%d calendars)",
            self._card_id, len(calendars)
        )

        now = datetime.now(timezone.utc)
        end = now + timedelta(days=time_window_days)

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(
                lambda cal: self._fetch_single_calendar(cal, now, end),
                calendars,
            ))

        all_events = [event for events in results for event in events]
        all_events.sort(key=lambda e: e.get("start", ""))

        self._logger.info(
            "Total events after merge/sort: %d", len(all_events)
        )

        self._store_events(all_events)
        self._logger.info(
            "Finished fetching calendar events for card %s", self._card_id
        )

    def _fetch_single_calendar(self, cal_config, start, end):
        url = cal_config["url"]
        auth_type = cal_config.get("auth_type", "basic")
        try:
            self._logger.info("Fetching calendar: %s", url)
            client = self._create_caldav_client(url, cal_config, auth_type)
            principal = client.principal()
            calendars = principal.calendars()

            if not calendars:
                self._logger.warning("No calendars found at %s", url)
                return []

            cal = calendars[0]
            events = cal.date_search(start, end)
            return self._parse_events(events)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch calendar: %s — %s", url, e)
            return []

    def _create_caldav_client(self, url, cal_config, auth_type):
        if auth_type == "bearer":
            bearer_token = cal_config.get("bearer_token", "")
            http_headers = {"Authorization": f"Bearer {bearer_token}"}
            return caldav.DAVClient(url=url, headers=http_headers)
        username = cal_config.get("username", "")
        password = cal_config.get("password", "")
        return caldav.DAVClient(url=url, username=username, password=password)

    def _parse_events(self, events):
        result = []
        for event in events:
            try:
                vevent = event.vobject_instance.vevent
                summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else ""
                dtstart = vevent.dtstart.value if hasattr(vevent, 'dtstart') else None

                is_allday = isinstance(dtstart, datetime) is False if dtstart else True

                if dtstart:
                    start_str = dtstart.isoformat() if isinstance(dtstart, datetime) else dtstart.isoformat()
                else:
                    start_str = ""

                result.append({
                    "summary": summary,
                    "start": start_str,
                    "is_allday": is_allday,
                })
            except (AttributeError, ValueError) as e:
                self._logger.warning("Failed to parse event: %s", e)

        self._logger.info("Got %d events from calendar", len(result))
        return result

    def _store_events(self, events):
        self._database.execute(
            "DELETE FROM calendar_events WHERE card_id = ?",
            (self._card_id,),
        )
        self._database.execute(
            "INSERT INTO calendar_events (card_id, events) VALUES (?, ?)",
            (self._card_id, json.dumps(events)),
        )

    @staticmethod
    def _compute_card_id(options):
        raw = json.dumps(options, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def card_style_rules() -> dict[str, str]:
        return {
            ".calendar-event": (
                "display: flex; gap: 0.75rem; padding: 0.5rem 0;"
                " border-bottom: 1px solid var(--border);"
            ),
            ".calendar-event:last-child": "border-bottom: none;",
            ".calendar-date": (
                "min-width: 4rem; font-size: 0.75rem;"
                " color: var(--text-muted); text-align: right;"
            ),
            ".calendar-date-day": "font-weight: 600; color: var(--text);",
            ".calendar-date-time": "font-size: 0.75rem;",
            ".calendar-summary": "font-size: 0.875rem; color: var(--text);",
            ".calendar-empty": (
                "text-align: center; padding: 1rem;"
                " color: var(--text-muted); font-size: 0.875rem;"
            ),
        }
