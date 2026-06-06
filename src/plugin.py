from abc import ABC, abstractmethod
from pathlib import Path

from apscheduler.triggers.cron import CronTrigger
from jinja2 import Environment, FileSystemLoader


class Plugin(ABC):
    @abstractmethod
    def setup(self, options, database, scheduler, logger):
        """Initialize the plugin for a card. Called once at startup."""

    @abstractmethod
    def render(self, options):
        """Return HTML string for the card."""

    @staticmethod
    @abstractmethod
    def init_schema(database):
        """Initialize database tables for this plugin. Called once at startup."""

    @staticmethod
    @abstractmethod
    def validate_options(options, card_idx, filename):
        """Validate plugin-specific options. Raise ConfigError if invalid."""

    def parse_schedule(self, schedule):
        return CronTrigger.from_crontab(schedule)

    @staticmethod
    def load_template(plugin_dir, template_name):
        return Environment(
            loader=FileSystemLoader(Path(plugin_dir))
        ).get_template(template_name)
