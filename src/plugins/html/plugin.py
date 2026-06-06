from src.plugin import Plugin


class HtmlPlugin(Plugin):
    def setup(self, options, database, scheduler, logger):
        pass

    def render(self, options):
        return options.get("html", "")

    @staticmethod
    def validate_options(options, card_idx, filename):
        pass
