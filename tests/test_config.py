import pytest
import yaml

from app.config import ConfigError, load_config, validate_config


class TestLoadConfig:
    def test_uses_config_yml_when_present(self, tmp_path, monkeypatch):
        config_data = {"title": "Test", "columns": [{"cards": [{"title": "A", "type": "link"}]}]}
        config_path = tmp_path / "config.yml"
        config_path.write_text(yaml.dump(config_data))

        starter_path = tmp_path / "starter.yaml"
        starter_path.write_text(yaml.dump({"title": "Default"}))

        monkeypatch.setattr("app.config.BASE_DIR", tmp_path)
        result = load_config()
        assert result["title"] == "Test"

    def test_falls_back_to_starter_yaml(self, tmp_path, monkeypatch):
        config_data = {"title": "Fallback", "columns": [{"cards": [{"title": "A", "type": "link"}]}]}
        starter_path = tmp_path / "starter.yaml"
        starter_path.write_text(yaml.dump(config_data))

        monkeypatch.setattr("app.config.BASE_DIR", tmp_path)
        result = load_config()
        assert result["title"] == "Fallback"

    def test_raises_when_both_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.config.BASE_DIR", tmp_path)
        with pytest.raises(ConfigError, match="No config file found"):
            load_config()

    def test_raises_on_invalid_yaml(self, tmp_path, monkeypatch):
        config_path = tmp_path / "starter.yaml"
        config_path.write_text(": invalid: yaml: {{{}}}}")

        monkeypatch.setattr("app.config.BASE_DIR", tmp_path)
        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config()

    def test_raises_on_empty_config(self, tmp_path, monkeypatch):
        config_path = tmp_path / "starter.yaml"
        config_path.write_text("")

        monkeypatch.setattr("app.config.BASE_DIR", tmp_path)
        with pytest.raises(ConfigError, match="empty"):
            load_config()


class TestValidateConfig:
    def test_valid_config(self):
        config = {"title": "Test", "columns": [{"cards": [{"title": "A", "type": "link"}]}]}
        validate_config(config)  # should not raise

    def test_missing_columns(self):
        with pytest.raises(ConfigError, match="columns"):
            validate_config({"title": "Test"})

    def test_empty_columns(self):
        with pytest.raises(ConfigError, match="non-empty"):
            validate_config({"columns": []})

    def test_missing_card_title(self):
        config = {"columns": [{"cards": [{"type": "link"}]}]}
        with pytest.raises(ConfigError, match="title is required"):
            validate_config(config)

    def test_missing_card_type(self):
        config = {"columns": [{"cards": [{"title": "A"}]}]}
        with pytest.raises(ConfigError, match="type is required"):
            validate_config(config)
