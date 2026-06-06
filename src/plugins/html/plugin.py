from src.plugin import Plugin


class HtmlPlugin(Plugin):
    @staticmethod
    def card_style_rules() -> dict[str, str]:
        """Return default CSS rules for HTML cards."""
        return {
            "img": "max-width: 100%; height: auto; border-radius: 0.375rem;",
            "a": "color: var(--link); text-decoration: underline;",
            "a:hover": "color: var(--link-hover);",
            "p": "margin-bottom: 0.5rem;",
            "p:last-child": "margin-bottom: 0;",
            "ul": "margin-left: 1.5rem; margin-bottom: 0.5rem; list-style-type: square;",
            "ol": "margin-left: 1.5rem; margin-bottom: 0.5rem;",
            "h1": "font-weight: 600; margin-bottom: 0.5rem;",
            "h2": "font-weight: 600; margin-bottom: 0.5rem;",
            "h3": "font-weight: 600; margin-bottom: 0.5rem;",
            "code": (
                "background: var(--code-bg); padding: 0.125rem 0.25rem;"
                " border-radius: 0.25rem; font-size: 0.875rem;"
            ),
            "pre": (
                "background: var(--code-bg); padding: 0.75rem;"
                " border-radius: 0.375rem; overflow-x: auto;"
                " margin-bottom: 0.5rem;"
            ),
            "pre code": "padding: 0; background: none;",
        }

    def setup(self, options, database, scheduler, logger):
        pass

    def render(self, options):
        return options.get("html", "")

    @staticmethod
    def validate_options(options, card_idx, filename):
        pass

    @staticmethod
    def init_schema(database):
        pass
