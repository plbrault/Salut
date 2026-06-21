from unittest.mock import patch

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.testclient import TestClient

from src.config import ConfigError
from src.main import app
from src.plugins.html import HtmlPlugin
from src.plugins.search import SearchPlugin


class TestServer:
    def test_index_returns_200(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200

    def test_index_contains_page_title(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "Salut" in response.text

    def test_index_contains_page_header(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "<h1>" in response.text

    def test_index_contains_time_emoji_script(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "time_emoji" in response.text

    def test_index_contains_date_script(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "Intl.DateTimeFormat" in response.text

    def test_index_contains_htmx(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "htmx.min.js" in response.text

    def test_index_contains_tailwind(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "tailwindcss.js" in response.text

    def test_index_contains_columns(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert 'id="container"' in response.text

    def test_html_lang_attr(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert '<html lang="' in response.text

    def test_header_has_css_styling(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "header h1" in response.text
            assert "font-size: 2.5rem" in response.text

    def test_page_header_rendered_with_safe(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "<h1>" in response.text
            assert "{{" not in response.text or "time_emoji" in response.text

    def test_card_divs_have_plugin_css_class(self):
        with patch("src.main.setup_card") as real_setup:
            def fake_setup(card, _db, _scheduler, _language, **_kwargs):
                name = card.get("plugin")
                if name == "html":
                    return HtmlPlugin()
                if name == "search":
                    return SearchPlugin()
                return None
            real_setup.side_effect = fake_setup
            with TestClient(app) as client:
                response = client.get("/")
                assert "card html-card" in response.text

    def test_plugin_style_rules_rendered(self):
        with patch("src.main.setup_card") as real_setup:
            def fake_setup(card, _db, _scheduler, _language, **_kwargs):
                name = card.get("plugin")
                if name == "html":
                    return HtmlPlugin()
                if name == "search":
                    return SearchPlugin()
                return None
            real_setup.side_effect = fake_setup
            with TestClient(app) as client:
                response = client.get("/")
                assert ".html-card" in response.text

    def test_theme_toggle_replaced_in_html(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "theme-toggle" in response.text
            assert "toggleTheme()" in response.text

    def test_theme_detection_script_present(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "prefers-color-scheme" in response.text
            assert "localStorage.getItem('theme')" in response.text

    def test_theme_css_custom_properties(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "--bg:" in response.text
            assert "--card-bg:" in response.text
            assert '[data-theme="dark"]' in response.text

    def test_theme_toggle_icons_defined(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "themeIcons" in response.text
            assert "sun:" in response.text
            assert "moon:" in response.text

    def test_dark_mode_css_variables_present(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "--link:" in response.text
            assert "--link-hover:" in response.text
            assert "--code-bg:" in response.text
            assert "--text-faint:" in response.text

    def test_card_title_uses_theme_color(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert ".card h3" in response.text
            assert "var(--text)" in response.text

    def test_favicon_rendered_when_present(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "favicon": "👋"}
            try:
                response = client.get("/")
                assert 'rel="icon"' in response.text
                assert "👋" in response.text
                assert "data:image/svg+xml" in response.text
            finally:
                app.state.config = original

    def test_favicon_not_rendered_when_absent(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {k: v for k, v in original.items() if k != "favicon"}
            try:
                response = client.get("/")
                assert 'rel="icon"' not in response.text
            finally:
                app.state.config = original

    def test_config_error_shows_error_page(self):
        error_msg = "Invalid YAML in config.yml: mapping values are not allowed here"
        with patch("src.main.load_config", side_effect=ConfigError(error_msg)):
            with TestClient(app) as client:
                response = client.get("/")
                assert response.status_code == 200
                assert "Configuration Error" in response.text
                assert "Invalid YAML in config.yml" in response.text

    def test_config_validation_error_shows_error_page(self):
        error_msg = "config.yml: 'language' must be a non-empty string."
        with patch("src.main.load_config", side_effect=ConfigError(error_msg)):
            with TestClient(app) as client:
                response = client.get("/")
                assert response.status_code == 200
                assert "Configuration Error" in response.text
                assert (
                    "'language' must be a non-empty string" in response.text
                    or "&#39;language&#39; must be a non-empty string" in response.text
                )

    def test_no_config_file_shows_error_page(self):
        error_msg = "No config file found. Create config.yml or starter.yml."
        with patch("src.main.load_config", side_effect=ConfigError(error_msg)):
            with TestClient(app) as client:
                response = client.get("/")
                assert response.status_code == 200
                assert "Configuration Error" in response.text
                assert "No config file found" in response.text

    def test_valid_config_no_error_page(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert "Configuration Error" not in response.text

    def test_scheduler_misfire_grace_time_unlimited(self):
        s = BackgroundScheduler(job_defaults={"misfire_grace_time": None})
        s.start()
        assert s._job_defaults["misfire_grace_time"] is None  # pylint: disable=protected-access
        s.shutdown(wait=False)
