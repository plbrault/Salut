from abc import ABC, abstractmethod

from apscheduler.triggers.cron import CronTrigger


class Plugin(ABC):
    @abstractmethod
    def setup(self, options, database, scheduler, logger):
        """Initialize the plugin for a card. Called once at startup."""

    @abstractmethod
    def render(self, options):
        """Return HTML string for the card."""

    def parse_schedule(self, schedule):
        return CronTrigger.from_crontab(schedule)
