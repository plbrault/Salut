import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import caldav
import requests
from icalendar import Calendar

from src.config import ConfigError
from src.plugin import Plugin

HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


class CalendarPlugin(Plugin):
    def __init__(self):
        super().__init__()
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


    @staticmethod
    def _validate_calendar_entry(cal, cal_idx, card_idx, filename):
        prefix = f"{filename}: cards[{card_idx}].options.calendars[{cal_idx}]"
        if not isinstance(cal, dict):
            raise ConfigError(f"{prefix} must be a mapping.")
        if not cal.get("url"):
            raise ConfigError(f"{prefix}.url is required.")
        if not cal.get("name") or not isinstance(cal["name"], str):
            raise ConfigError(f"{prefix}.name is required and must be a string.")
        color = cal.get("color")
        if color is not None:
            if not isinstance(color, str) or not HEX_COLOR_RE.match(color):
                raise ConfigError(
                    f"{prefix}.color must be a hex color string (e.g., '#3b82f6')."
                )
        link_url = cal.get("link_url")
        if link_url is not None:
            raise ConfigError(
                f"{prefix}.link_url is no longer supported. "
                "Event URLs are now extracted automatically from the calendar."
            )
        cal_type = cal.get("type", "caldav")
        if cal_type not in ("caldav", "ics"):
            raise ConfigError(f"{prefix}.type must be 'caldav' or 'ics'.")
        auth_type = cal.get("auth_type", "none")
        if auth_type not in ("none", "basic", "bearer"):
            raise ConfigError(f"{prefix}.auth_type must be 'none', 'basic', or 'bearer'.")
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

    def setup(self, card_id, options, database, scheduler, logger):
        self._database = database
        self._logger = logger
        self._card_id = card_id if card_id else self._compute_card_id(options)

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

    def render(self, cards):
        results = []
        for card in cards:
            options = card["options"]
            card_id = card["card_id"]
            row = self._database.fetch_one(
                "SELECT events FROM calendar_events WHERE card_id = ?",
                (card_id,),
            )
            if not row:
                results.append(f'<p style="color: var(--text-muted)">{self.t("no_events")}</p>')
                continue

            events = json.loads(row["events"])
            max_events = options.get("max_events", 10)

            events.sort(key=lambda e: e.get("start", ""))
            events = events[:max_events]

            if not events:
                results.append(f'<p style="color: var(--text-muted)">{self.t("no_events")}</p>')
                continue

            html = self._template.render(events=events)
            results.append(html)
        return results

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
        cal_type = cal_config.get("type", "caldav")
        if cal_type == "ics":
            return self._fetch_ics(cal_config, start, end)
        return self._fetch_caldav(cal_config, start, end)

    def _fetch_caldav(self, cal_config, start, end):
        url = cal_config["url"]
        auth_type = cal_config.get("auth_type", "none")
        try:
            self._logger.info("Fetching CalDAV calendar: %s", url)
            client = self._create_caldav_client(url, cal_config, auth_type)
            cal = caldav.Calendar(url=url, client=client)
            # pylint: disable=deprecated-method
            events = cal.date_search(start, end)
            return self._parse_caldav_events(events, cal_config)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch CalDAV calendar: %s — %s", url, e)
            return []

    def _fetch_ics(self, cal_config, start, end):
        url = cal_config["url"]
        try:
            self._logger.info("Fetching ICS calendar: %s", url)
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            cal = Calendar.from_ical(response.text)
            return self._parse_ics_events(cal, start, end, cal_config)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch ICS calendar: %s — %s", url, e)
            return []

    def _create_caldav_client(self, url, cal_config, auth_type):
        if auth_type == "bearer":
            bearer_token = cal_config.get("bearer_token", "")
            http_headers = {"Authorization": f"Bearer {bearer_token}"}
            return caldav.DAVClient(url=url, headers=http_headers)
        if auth_type == "basic":
            username = cal_config.get("username", "")
            password = cal_config.get("password", "")
            return caldav.DAVClient(url=url, username=username, password=password)
        return caldav.DAVClient(url=url)

    @staticmethod
    def _is_nextcloud(cal_url):
        return "/dav/calendars/" in cal_url or "/remote.php/dav/" in cal_url

    @staticmethod
    def _build_nextcloud_event_url(cal_url, uid):
        parsed = urlparse(cal_url)
        return f"{parsed.scheme}://{parsed.netloc}/apps/calendar/object/{uid}"

    def _parse_caldav_events(self, events, cal_config):
        result = []
        cal_url = cal_config.get("url", "")
        is_nc = self._is_nextcloud(cal_url)
        for event in events:
            try:
                vevent = event.vobject_instance.vevent
                summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else ""
                dtstart = vevent.dtstart.value if hasattr(vevent, 'dtstart') else None
                url = str(vevent.url.value) if hasattr(vevent, 'url') else None

                if url is None and is_nc:
                    uid = str(vevent.uid.value) if hasattr(vevent, 'uid') else None
                    if uid:
                        url = self._build_nextcloud_event_url(cal_url, uid)

                is_allday = isinstance(dtstart, datetime) is False if dtstart else True
                start_str = dtstart.isoformat() if dtstart else ""

                result.append({
                    "summary": summary,
                    "start": start_str,
                    "is_allday": is_allday,
                    "calendar_name": cal_config["name"],
                    "calendar_color": cal_config.get("color"),
                    "url": url,
                })
            except (AttributeError, ValueError) as e:
                self._logger.warning("Failed to parse CalDAV event: %s", e)

        self._logger.info("Got %d events from CalDAV calendar", len(result))
        return result

    def _parse_ics_events(self, cal, start, end, cal_config):  # pylint: disable=too-many-locals
        result = []
        for component in cal.walk():
            if component.name != "VEVENT":
                continue
            try:
                summary = str(component.get("SUMMARY", ""))
                dtstart = component.get("DTSTART")
                url = str(component.get("URL")) if component.get("URL") is not None else None

                if dtstart is None:
                    continue

                dtstart_val = dtstart.dt
                is_allday = not isinstance(dtstart_val, datetime)
                start_str = dtstart_val.isoformat()

                start_dt = datetime.fromisoformat(start_str) if start_str else None
                if start_dt:
                    if is_allday:
                        start_aware = start_dt.replace(tzinfo=timezone.utc)
                    elif start_dt.tzinfo is None:
                        start_aware = start_dt.replace(tzinfo=timezone.utc)
                    else:
                        start_aware = start_dt
                    if start_aware < start or start_aware > end:
                        continue

                result.append({
                    "summary": summary,
                    "start": start_str,
                    "is_allday": is_allday,
                    "calendar_name": cal_config["name"],
                    "calendar_color": cal_config.get("color"),
                    "url": url,
                })
            except (AttributeError, ValueError) as e:
                self._logger.warning("Failed to parse ICS event: %s", e)

        self._logger.info("Got %d events from ICS calendar", len(result))
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
                "white-space: nowrap; font-size: 0.75rem;"
                " color: var(--text-muted); text-align: right;"
            ),
            ".calendar-date-day": "font-weight: 600; color: var(--text);",
            ".calendar-date-time": "font-size: 0.75rem;",
            ".calendar-event-body": "display: flex; flex-direction: column; gap: 0.125rem; min-width: 0;",
            ".calendar-summary": "font-size: 0.875rem; color: var(--text);",
            ".calendar-name": "font-size: 0.75rem; color: var(--text-muted);",
            ".calendar-name-dot": (
                "display: inline-block; width: 0.5rem; height: 0.5rem;"
                " border-radius: 50%; margin-right: 0.25rem; vertical-align: middle;"
            ),
            ".calendar-empty": (
                "text-align: center; padding: 1rem;"
                " color: var(--text-muted); font-size: 0.875rem;"
            ),
        }
