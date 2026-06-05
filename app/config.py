from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def load_config():
    config_path = BASE_DIR / "config.yml"
    if not config_path.exists():
        config_path = BASE_DIR / "starter.yaml"

    if not config_path.exists():
        raise ConfigError("No config file found. Create config.yml or starter.yaml.")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path.name}: {e}") from e

    if config is None:
        raise ConfigError(f"Config file {config_path.name} is empty.")

    validate_config(config, config_path.name)
    return config


def validate_config(config, filename="config"):
    if not isinstance(config, dict):
        raise ConfigError(f"{filename}: config must be a mapping (key-value pairs).")

    columns = config.get("columns")
    if not columns or not isinstance(columns, list) or len(columns) == 0:
        raise ConfigError(f"{filename}: 'columns' must be a non-empty array.")

    for col_idx, column in enumerate(columns):
        if not isinstance(column, dict):
            raise ConfigError(
                f"{filename}: columns[{col_idx}] must be a mapping."
            )

        cards = column.get("cards")
        if not cards or not isinstance(cards, list) or len(cards) == 0:
            raise ConfigError(
                f"{filename}: columns[{col_idx}].cards must be a non-empty array."
            )

        for card_idx, card in enumerate(cards):
            if not isinstance(card, dict):
                raise ConfigError(
                    f"{filename}: columns[{col_idx}].cards[{card_idx}] must be a mapping."
                )

            if not card.get("title"):
                raise ConfigError(
                    f"{filename}: columns[{col_idx}].cards[{card_idx}].title is required."
                )

            if not card.get("type"):
                raise ConfigError(
                    f"{filename}: columns[{col_idx}].cards[{card_idx}].type is required."
                )
