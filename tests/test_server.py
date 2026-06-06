from unittest.mock import patch

from fastapi.testclient import TestClient

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
            assert "Chris" in response.text

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
            def fake_setup(card, _db, _scheduler):
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
            def fake_setup(card, _db, _scheduler):
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
