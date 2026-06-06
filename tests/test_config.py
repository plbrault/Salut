import pytest
import yaml

from src.config import ConfigError, load_config, validate_config


def _make_config(**overrides):
    """Create a valid config with optional overrides."""
    config = {
        "page_title": "Test",
        "page_header": "<h1>Hi ${user_info.short_name} {{time_emoji}}</h1><span>{{date}}</span>",
        "language": "en",
        "user_info": {"short_name": "A", "long_name": "B"},
        "columns": 3,
        "cards": [{"title": "A", "plugin": "html", "options": {"html": "<p>Test</p>"}}],
    }
    config.update(overrides)
    return config


class TestLoadConfig:
    def test_uses_config_yml_when_present(self, tmp_path, monkeypatch):
        config_data = _make_config(page_title="Test")
        config_path = tmp_path / "config.yml"
        config_path.write_text(yaml.dump(config_data))

        starter_path = tmp_path / "starter.yml"
        starter_path.write_text(yaml.dump(_make_config(page_title="Default")))

        monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
        result = load_config()
        assert result["page_title"] == "Test"

    def test_falls_back_to_starter_yaml(self, tmp_path, monkeypatch):
        config_data = _make_config(page_title="Fallback")
        starter_path = tmp_path / "starter.yml"
        starter_path.write_text(yaml.dump(config_data))

        monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
        result = load_config()
        assert result["page_title"] == "Fallback"

    def test_raises_when_both_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
        with pytest.raises(ConfigError, match="No config file found"):
            load_config()

    def test_raises_on_invalid_yaml(self, tmp_path, monkeypatch):
        config_path = tmp_path / "starter.yml"
        config_path.write_text(": invalid: yaml: {{{}}}}")

        monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config()

    def test_raises_on_empty_config(self, tmp_path, monkeypatch):
        config_path = tmp_path / "starter.yml"
        config_path.write_text("")

        monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
        with pytest.raises(ConfigError, match="empty"):
            load_config()


class TestValidateConfig:
    def test_valid_config(self):
        validate_config(_make_config())  # should not raise

    def test_missing_page_title(self):
        with pytest.raises(ConfigError, match="page_title"):
            validate_config(_make_config(page_title=None))

    def test_missing_page_header(self):
        with pytest.raises(ConfigError, match="page_header"):
            validate_config(_make_config(page_header=None))

    def test_invalid_page_title_type(self):
        with pytest.raises(ConfigError, match="page_title"):
            validate_config(_make_config(page_title=123))

    def test_invalid_page_header_type(self):
        with pytest.raises(ConfigError, match="page_header"):
            validate_config(_make_config(page_header=[]))


class TestValidateLanguage:
    def test_missing_language(self):
        with pytest.raises(ConfigError, match="language"):
            validate_config(_make_config(language=None))

    def test_invalid_language_type(self):
        with pytest.raises(ConfigError, match="language"):
            validate_config(_make_config(language=123))

    def test_invalid_language_code(self):
        with pytest.raises(ConfigError, match="language"):
            validate_config(_make_config(language="invalid"))

    def test_valid_bcp47_tag(self):
        validate_config(_make_config(language="fr-CA"))  # should not raise

    def test_valid_simple_code_en(self):
        config = _make_config(language="en")
        validate_config(config)
        assert config["language"] == "en-US"

    def test_valid_simple_code_fr(self):
        config = _make_config(language="fr")
        validate_config(config)
        assert config["language"] == "fr-FR"


class TestValidateUserInfo:
    def test_missing_user_info(self):
        with pytest.raises(ConfigError, match="user_info"):
            validate_config(_make_config(user_info=None))

    def test_invalid_user_info_type(self):
        with pytest.raises(ConfigError, match="user_info"):
            validate_config(_make_config(user_info="string"))

    def test_missing_short_name(self):
        with pytest.raises(ConfigError, match="short_name"):
            validate_config(_make_config(user_info={"long_name": "B"}))

    def test_missing_long_name(self):
        with pytest.raises(ConfigError, match="long_name"):
            validate_config(_make_config(user_info={"short_name": "A"}))

    def test_invalid_short_name_type(self):
        with pytest.raises(ConfigError, match="short_name"):
            validate_config(_make_config(user_info={"short_name": 123, "long_name": "B"}))

    def test_invalid_long_name_type(self):
        with pytest.raises(ConfigError, match="long_name"):
            validate_config(_make_config(user_info={"short_name": "A", "long_name": []}))


class TestValidateColumns:
    def test_missing_columns(self):
        with pytest.raises(ConfigError, match="columns"):
            validate_config(_make_config(columns=None))

    def test_non_integer_columns(self):
        with pytest.raises(ConfigError, match="positive integer"):
            validate_config(_make_config(columns="three"))

    def test_zero_columns(self):
        with pytest.raises(ConfigError, match="positive integer"):
            validate_config(_make_config(columns=0))

    def test_missing_cards(self):
        with pytest.raises(ConfigError, match="cards"):
            validate_config(_make_config(cards=None))

    def test_empty_cards(self):
        with pytest.raises(ConfigError, match="non-empty"):
            validate_config(_make_config(cards=[]))

    def test_missing_card_title(self):
        with pytest.raises(ConfigError, match="title is required"):
            validate_config(_make_config(cards=[{"plugin": "html"}]))

    def test_missing_card_plugin(self):
        with pytest.raises(ConfigError, match="plugin is required"):
            validate_config(_make_config(cards=[{"title": "A"}]))
