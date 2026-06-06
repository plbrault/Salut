from abc import ABC, abstractmethod
from pathlib import Path

from apscheduler.triggers.cron import CronTrigger
from jinja2 import Environment, FileSystemLoader

from src.i18n import _load_translations


class Plugin(ABC):
    def __init__(self):
        self._translations = {}

    @staticmethod
    def card_style_rules() -> dict[str, str]:
        """Return CSS rules for this plugin's card class.

        Returns a dict mapping sub-selectors to CSS declarations.
        Keys are relative to the card's CSS class (e.g. ``"img"`` becomes
        ``.html-card img``). Return an empty dict for no custom styling.
        """
        return {}

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

    @staticmethod
    def parse_schedule(schedule):
        return CronTrigger.from_crontab(schedule)

    @staticmethod
    def load_template(plugin_dir, template_name):
        return Environment(
            loader=FileSystemLoader(Path(plugin_dir))
        ).get_template(template_name)

    def load_i18n(self, language):
        """Load plugin-specific i18n translations with English fallback."""
        module_parts = type(self).__module__.split(".")
        plugin_name = module_parts[-2]
        i18n_dir = Path(__file__).resolve().parent / "plugins" / plugin_name / "i18n"
        self._translations = _load_translations(i18n_dir, language)

    def t(self, key):
        """Return translated string for key, or key name as fallback."""
        return self._translations.get(key, key)

    def set_translations(self, translations):
        """Set translations directly (for testing)."""
        self._translations = translations
