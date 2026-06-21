import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.config import ConfigError
from src.plugin import Plugin


class GithubPlugin(Plugin):
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
        if options is None:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options is required for GitHub Notifications plugin."
            )

        token = options.get("token")
        if not token:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.token is required."
            )

        schedule = options.get("schedule")
        if schedule is not None:
            if not isinstance(schedule, str):
                raise ConfigError(
                    f"{filename}: cards[{card_idx}].options.schedule must be a string."
                )
            parts = schedule.strip().split()
            if len(parts) not in (5, 6):
                raise ConfigError(
                    f"{filename}: cards[{card_idx}].options.schedule must be a valid cron expression (5 or 6 fields)."
                )

        max_items = options.get("max_items")
        if max_items is not None:
            if not isinstance(max_items, int) or max_items < 1:
                raise ConfigError(
                    f"{filename}: cards[{card_idx}].options.max_items must be a positive integer."
                )

    @staticmethod
    def init_schema(database):
        database.execute(
            """
            CREATE TABLE IF NOT EXISTS github_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL DEFAULT '',
                thread_id INTEGER NOT NULL,
                repo_name TEXT NOT NULL,
                subject_title TEXT NOT NULL,
                reason TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                web_url TEXT NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    def setup(self, options, database, scheduler, logger, *, card_id=None,
              card_ids=None):
        self._database = database
        self._logger = logger
        self._card_id = card_id if card_id else self._compute_card_id(options)

        token = options.get("token")
        if not token:
            return

        schedule = options.get("schedule", "*/5 * * * *")

        self._fetch_notifications(options)
        scheduler.add_job(
            self._fetch_notifications,
            trigger=self.parse_schedule(schedule),
            args=[options],
            id=f"github_notifications_{self._card_id}",
            replace_existing=True,
        )

    def render(self, cards):
        results = []
        for card in cards:
            options = card["options"]
            card_id = card["card_id"]
            token = options.get("token")
            if not token:
                results.append(
                    '<p class="text-sm" style="color: var(--text-muted)">'
                    "GitHub token not configured. "
                    "Add <code>token</code> to your card options "
                    "(recommended: use <code>${secrets.github_token}</code>)."
                    "</p>"
                )
                continue

            max_items = options.get("max_items", 10)
            rows = self._database.fetch_all(
                "SELECT * FROM github_notifications WHERE card_id = ? ORDER BY updated_at DESC LIMIT ?",
                (card_id, max_items),
            )

            notifications = []
            for row in rows:
                notifications.append({
                    "repo_name": row["repo_name"],
                    "subject_title": row["subject_title"],
                    "reason": row["reason"],
                    "time_ago": self._time_ago(row["updated_at"]),
                    "web_url": row["web_url"],
                })

            results.append(self._template.render(
                notifications=notifications,
                no_notifications_label=self.t("no_notifications"),
            ))
        return results

    def _fetch_notifications(self, options):
        try:
            token = options["token"]
            self._logger.info("Fetching GitHub notifications for card %s", self._card_id)

            response = requests.get(
                "https://api.github.com/notifications",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10,
            )
            response.raise_for_status()

            self._delete_previous_notifications()

            for thread in response.json():
                thread_id = thread["id"]
                repo_name = thread["repository"]["full_name"]
                subject_title = thread["subject"]["title"]
                reason = self._format_reason(thread["reason"])
                updated_at = thread["updated_at"]
                web_url = self._build_web_url(thread["subject"]["url"])

                self._store_notification(
                    card_id=self._card_id,
                    thread_id=thread_id,
                    repo_name=repo_name,
                    subject_title=subject_title,
                    reason=reason,
                    updated_at=updated_at,
                    web_url=web_url,
                )

            self._logger.info("GitHub notifications fetched for card %s", self._card_id)
        except Exception as e:  # pylint: disable=broad-except
            self._logger.warning("Failed to fetch GitHub notifications: %s", e)

    def _delete_previous_notifications(self):
        self._database.execute(
            "DELETE FROM github_notifications WHERE card_id = ?",
            (self._card_id,),
        )

    def _store_notification(self, **kwargs):
        self._database.execute(
            """
            INSERT INTO github_notifications
            (card_id, thread_id, repo_name, subject_title, reason, updated_at, web_url)
            VALUES (:card_id, :thread_id, :repo_name, :subject_title, :reason, :updated_at, :web_url)
            """,
            kwargs,
        )

    @staticmethod
    def _build_web_url(api_url):
        url = api_url.replace("https://api.github.com/repos/", "https://github.com/")
        url = url.replace("/pulls/", "/pull/")
        url = url.replace("/issues/", "/issues/")
        if url.endswith(".patch"):
            url = url[:-6]
        if url.endswith(".json"):
            url = url[:-5]
        return url

    @staticmethod
    def _format_reason(reason):
        return reason.replace("_", " ").lower()

    @staticmethod
    def _time_ago(iso_timestamp):
        try:
            updated = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            diff = now - updated
            seconds = int(diff.total_seconds())
            if seconds < 60:
                return "just now"
            if seconds < 3600:
                minutes = seconds // 60
                return f"{minutes}m ago"
            if seconds < 86400:
                hours = seconds // 3600
                return f"{hours}h ago"
            days = seconds // 86400
            return f"{days}d ago"
        except (ValueError, TypeError):
            return ""

    @staticmethod
    def _compute_card_id(options):
        raw = json.dumps(options, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
