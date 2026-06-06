from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent

LANGUAGE_DEFAULTS = {
    "en": "en-US",
    "fr": "fr-FR",
}


class ConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def load_config():
    config_path = BASE_DIR / "config.yml"
    if not config_path.exists():
        config_path = BASE_DIR / "starter.yml"

    if not config_path.exists():
        raise ConfigError("No config file found. Create config.yml or starter.yml.")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path.name}: {e}") from e

    if config is None:
        raise ConfigError(f"Config file {config_path.name} is empty.")

    validate_config(config, config_path.name)
    return config


def _validate_required_string(config, key, filename):
    """Validate that a key exists and is a non-empty string."""
    value = config.get(key)
    if not value or not isinstance(value, str):
        raise ConfigError(f"{filename}: '{key}' must be a non-empty string.")


def _validate_user_info(config, filename):
    """Validate user_info object and its required fields."""
    user_info = config.get("user_info")
    if not user_info or not isinstance(user_info, dict):
        raise ConfigError(f"{filename}: 'user_info' must be a mapping.")

    _validate_required_string(user_info, "short_name", f"{filename}.user_info")
    _validate_required_string(user_info, "long_name", f"{filename}.user_info")


def _validate_language(config, filename):
    """Validate and normalize language code."""
    language = config.get("language")
    if not language or not isinstance(language, str):
        raise ConfigError(f"{filename}: 'language' must be a non-empty string.")

    if "-" in language:
        parts = language.split("-")
        if len(parts) != 2 or not all(parts):
            raise ConfigError(f"{filename}: 'language' must be a valid BCP 47 tag.")
    elif language not in LANGUAGE_DEFAULTS:
        raise ConfigError(
            f"{filename}: 'language' must be a BCP 47 tag or simple code "
            f"({', '.join(LANGUAGE_DEFAULTS.keys())})."
        )
    else:
        config["language"] = LANGUAGE_DEFAULTS[language]


def _validate_card(card, card_idx, filename):
    """Validate a single card."""
    if not isinstance(card, dict):
        raise ConfigError(
            f"{filename}: cards[{card_idx}] must be a mapping."
        )

    if not card.get("title"):
        raise ConfigError(
            f"{filename}: cards[{card_idx}].title is required."
        )

    if not card.get("plugin"):
        raise ConfigError(
            f"{filename}: cards[{card_idx}].plugin is required."
        )

    if "options" in card and not isinstance(card["options"], dict):
        raise ConfigError(
            f"{filename}: cards[{card_idx}].options must be a mapping."
        )

    if "colspan" in card:
        colspan = card["colspan"]
        if not isinstance(colspan, int) or colspan < 1:
            raise ConfigError(
                f"{filename}: cards[{card_idx}].colspan must be a positive integer."
            )

    if card.get("plugin") == "rss":
        _validate_rss_card(card, card_idx, filename)


def _validate_rss_card(card, card_idx, filename):
    """Validate RSS-specific card options."""
    options = card.get("options", {})
    if not options:
        raise ConfigError(
            f"{filename}: cards[{card_idx}].options is required for RSS plugin."
        )

    feeds = options.get("feeds")
    if not feeds or not isinstance(feeds, list) or len(feeds) == 0:
        raise ConfigError(
            f"{filename}: cards[{card_idx}].options.feeds must be a non-empty list."
        )

    refresh = options.get("refresh")
    if not refresh:
        raise ConfigError(
            f"{filename}: cards[{card_idx}].options.refresh is required (cron expression)."
        )

    if not isinstance(refresh, str):
        raise ConfigError(
            f"{filename}: cards[{card_idx}].options.refresh must be a string."
        )

    parts = refresh.strip().split()
    if len(parts) not in (5, 6):
        raise ConfigError(
            f"{filename}: cards[{card_idx}].options.refresh must be a valid cron expression (5 or 6 fields)."
        )


def _validate_cards(config, filename):
    """Validate cards list."""
    columns = config.get("columns")
    if not isinstance(columns, int) or columns < 1:
        raise ConfigError(f"{filename}: 'columns' must be a positive integer.")

    cards = config.get("cards")
    if not cards or not isinstance(cards, list) or len(cards) == 0:
        raise ConfigError(f"{filename}: 'cards' must be a non-empty list.")

    for card_idx, card in enumerate(cards):
        _validate_card(card, card_idx, filename)


def validate_config(config, filename="config"):
    if not isinstance(config, dict):
        raise ConfigError(f"{filename}: config must be a mapping (key-value pairs).")

    _validate_required_string(config, "page_title", filename)
    _validate_required_string(config, "page_header", filename)
    _validate_language(config, filename)
    _validate_user_info(config, filename)
    _validate_cards(config, filename)
