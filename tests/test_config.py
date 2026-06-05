import pytest
import yaml

from app.config import ConfigError, load_config, validate_config


class TestLoadConfig:
    def test_uses_config_yml_when_present(self, tmp_path, monkeypatch):
        config_data = {
            "page_title": "Test",
            "page_header": "Hi ${user_info.short_name}",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        config_path = tmp_path / "config.yml"
        config_path.write_text(yaml.dump(config_data))

        starter_path = tmp_path / "starter.yaml"
        starter_data = {
            "page_title": "Default",
            "page_header": "Hi ${user_info.short_name}",
            "user_info": {"short_name": "X", "long_name": "Y"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        starter_path.write_text(yaml.dump(starter_data))

        monkeypatch.setattr("app.config.BASE_DIR", tmp_path)
        result = load_config()
        assert result["page_title"] == "Test"

    def test_falls_back_to_starter_yaml(self, tmp_path, monkeypatch):
        config_data = {
            "page_title": "Fallback",
            "page_header": "Hi ${user_info.short_name}",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        starter_path = tmp_path / "starter.yaml"
        starter_path.write_text(yaml.dump(config_data))

        monkeypatch.setattr("app.config.BASE_DIR", tmp_path)
        result = load_config()
        assert result["page_title"] == "Fallback"

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
        config = {
            "page_title": "Test",
            "page_header": "Hi ${user_info.short_name}",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        validate_config(config)  # should not raise

    def test_missing_page_title(self):
        config = {
            "page_header": "Hi",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="page_title"):
            validate_config(config)

    def test_missing_page_header(self):
        config = {
            "page_title": "Test",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="page_header"):
            validate_config(config)

    def test_missing_user_info(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="user_info"):
            validate_config(config)

    def test_missing_short_name(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": {"long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="short_name"):
            validate_config(config)

    def test_missing_long_name(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": {"short_name": "A"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="long_name"):
            validate_config(config)

    def test_missing_columns(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": {"short_name": "A", "long_name": "B"},
        }
        with pytest.raises(ConfigError, match="columns"):
            validate_config(config)

    def test_empty_columns(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [],
        }
        with pytest.raises(ConfigError, match="non-empty"):
            validate_config(config)

    def test_missing_card_title(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="title is required"):
            validate_config(config)

    def test_missing_card_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"title": "A"}]}],
        }
        with pytest.raises(ConfigError, match="type is required"):
            validate_config(config)

    def test_invalid_page_title_type(self):
        config = {
            "page_title": 123,
            "page_header": "Hi",
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="page_title"):
            validate_config(config)

    def test_invalid_page_header_type(self):
        config = {
            "page_title": "Test",
            "page_header": [],
            "user_info": {"short_name": "A", "long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="page_header"):
            validate_config(config)

    def test_invalid_user_info_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": "string",
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="user_info"):
            validate_config(config)

    def test_invalid_short_name_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": {"short_name": 123, "long_name": "B"},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="short_name"):
            validate_config(config)

    def test_invalid_long_name_type(self):
        config = {
            "page_title": "Test",
            "page_header": "Hi",
            "user_info": {"short_name": "A", "long_name": []},
            "columns": [{"cards": [{"title": "A", "type": "link"}]}],
        }
        with pytest.raises(ConfigError, match="long_name"):
            validate_config(config)
