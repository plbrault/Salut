from pathlib import Path

from src.config import ConfigError
from src.plugin import Plugin


class SearchPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self._template = self.load_template(Path(__file__).resolve().parent, "template.html")

    @staticmethod
    def validate_options(options, card_idx, filename):
        if not options:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options is required for search plugin."
            )

        provider = options.get("provider")
        if not provider:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.provider is required."
            )

        if provider not in ("duckduckgo", "wikipedia"):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.provider must be 'duckduckgo' or 'wikipedia'."
            )

        language = options.get("language")
        if language is not None and not isinstance(language, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.language must be a string."
            )

        button_text = options.get("button_text")
        if button_text is not None and not isinstance(button_text, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.button_text must be a string."
            )

        placeholder_text = options.get("placeholder_text")
        if placeholder_text is not None and not isinstance(placeholder_text, str):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.placeholder_text must be a string."
            )

        results_in_new_tab = options.get("results_in_new_tab")
        if results_in_new_tab is not None and not isinstance(results_in_new_tab, bool):
            raise ConfigError(
                f"{filename}: cards[{card_idx}].options.results_in_new_tab must be a boolean."
            )

    def setup(self, options, card_id, database, scheduler, logger):
        pass

    def render(self, cards):
        results = []
        for card in cards:
            options = card["options"]
            provider = options.get("provider", "duckduckgo")
            button_text = options.get("button_text") or self.t("search")
            placeholder_text = options.get("placeholder_text") or self.t("search")
            results_in_new_tab = options.get("results_in_new_tab", False)
            language = options.get("language", "en")

            if provider == "wikipedia":
                action_url = f"https://{language}.wikipedia.org/w/index.php"
                query_param = "search"
            else:
                action_url = "https://duckduckgo.com/"
                query_param = "q"

            results.append(self._template.render(
                action_url=action_url,
                query_param=query_param,
                button_text=button_text,
                placeholder_text=placeholder_text,
                results_in_new_tab=results_in_new_tab,
            ))
        return results

    @staticmethod
    def init_schema(database):
        pass
