from fastapi.testclient import TestClient

from app.main import app


class TestServer:
    def test_index_returns_200(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200

    def test_index_contains_title(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "Salut" in response.text

    def test_index_contains_htmx(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert "htmx.org" in response.text

    def test_index_contains_columns(self):
        with TestClient(app) as client:
            response = client.get("/")
            assert 'class="columns"' in response.text
