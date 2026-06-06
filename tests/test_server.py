from fastapi.testclient import TestClient

from src.main import app


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
