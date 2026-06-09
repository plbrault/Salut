from fastapi.testclient import TestClient

from src.main import app
from src.admin import create_session_cookie, verify_session_cookie, COOKIE_NAME, log_buffer


class TestAdminAuth:
    def test_admin_returns_error_without_password(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {k: v for k, v in original.items() if k != "admin_password"}
            try:
                response = client.get("/admin")
                assert response.status_code == 403
                assert "Admin Not Enabled" in response.text
                assert "Set <code>admin_password</code> in your config" in response.text
            finally:
                app.state.config = original

    def test_admin_returns_error_with_empty_secrets_reference(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": ""}
            try:
                response = client.get("/admin")
                assert response.status_code == 403
                assert "Admin Not Enabled" in response.text
                assert "secrets.yml" in response.text
            finally:
                app.state.config = original

    def test_admin_login_page_shows_with_password(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                response = client.get("/admin/login")
                assert response.status_code == 200
                assert "Password" in response.text
            finally:
                app.state.config = original

    def test_admin_login_with_correct_password(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                response = client.post("/admin/login", json={"password": "secret"}, follow_redirects=False)
                assert response.status_code == 302
                assert response.headers["location"] == "/admin"
                assert COOKIE_NAME in response.cookies
            finally:
                app.state.config = original

    def test_admin_login_with_incorrect_password(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                response = client.post("/admin/login", json={"password": "wrong"})
                assert response.status_code == 200
                assert "Invalid password" in response.text
            finally:
                app.state.config = original

    def test_admin_redirects_to_login_when_not_authenticated(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                response = client.get("/admin", follow_redirects=False)
                assert response.status_code == 302
                assert response.headers["location"] == "/admin/login"
            finally:
                app.state.config = original

    def test_admin_page_loads_when_authenticated(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                response = client.get("/admin")
                assert response.status_code == 200
                assert "Salut Admin" in response.text
            finally:
                app.state.config = original

    def test_admin_logout_clears_cookie(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                response = client.post("/admin/logout", follow_redirects=False)
                assert response.status_code == 302
                assert response.headers["location"] == "/admin/login"
            finally:
                app.state.config = original

    def test_admin_endpoint_returns_401_without_session(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                response = client.get("/admin/config", follow_redirects=False)
                assert response.status_code == 302
                assert response.headers["location"] == "/admin/login"
            finally:
                app.state.config = original


class TestSessionCookie:
    def test_session_cookie_creation_and_verification(self):
        cookie_value = create_session_cookie("password123")
        assert verify_session_cookie(cookie_value) is True

    def test_session_cookie_verification_with_wrong_value(self):
        cookie = create_session_cookie("password123")
        assert verify_session_cookie("wrong|signature") is False

    def test_session_cookie_verification_with_none(self):
        assert verify_session_cookie(None) is False

    def test_session_cookie_verification_with_empty_string(self):
        assert verify_session_cookie("") is False

    def test_session_cookie_verification_with_malformed(self):
        assert verify_session_cookie("nopipe") is False


class TestAdminConfigEditor:
    def test_get_config_returns_content(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                response = client.get("/admin/config")
                assert response.status_code == 200
                assert "content" in response.json()
            finally:
                app.state.config = original

    def test_validate_valid_yaml(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                valid_yaml = """
page_title: Test
page_header: "<h1>Test</h1>"
language: en
user_info:
  short_name: Test
  long_name: Test User
columns: 1
cards:
  - title: Test
    plugin: html
    options:
      html: "Hello"
"""
                response = client.post("/admin/validate", json={"content": valid_yaml})
                assert response.status_code == 200
                assert response.json()["status"] == "ok"
            finally:
                app.state.config = original

    def test_validate_invalid_yaml_syntax(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                invalid_yaml = "page_title: Test\n  invalid: indentation"
                response = client.post("/admin/validate", json={"content": invalid_yaml})
                assert response.status_code == 400
                assert "error" in response.json()
            finally:
                app.state.config = original

    def test_validate_invalid_config(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                invalid_config = "page_title: Test"
                response = client.post("/admin/validate", json={"content": invalid_config})
                assert response.status_code == 400
                assert "error" in response.json()
            finally:
                app.state.config = original


class TestAdminLogs:
    def test_logs_endpoint_returns_list(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                response = client.get("/admin/logs")
                assert response.status_code == 200
                assert isinstance(response.json(), list)
            finally:
                app.state.config = original

    def test_logs_endpoint_captures_log_entries(self):
        import logging
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                log_buffer.clear()
                logging.info("Test log message from admin tests")
                response = client.get("/admin/logs")
                assert response.status_code == 200
                logs = response.json()
                assert len(logs) > 0
                assert any("Test log message" in entry.get("message", "") for entry in logs)
            finally:
                app.state.config = original
                log_buffer.clear()


class TestAdminReloadAndRestartUpdate:
    def test_reload_preserves_database(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                db = app.state.database
                db.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)")
                db.execute("INSERT INTO test_table (id) VALUES (1)")
                response = client.post("/admin/reload")
                assert response.status_code == 200
                assert response.json()["status"] == "ok"
                result = db.fetch_all("SELECT * FROM test_table")
                assert len(result) == 1
            finally:
                app.state.config = original
                db.execute("DROP TABLE IF EXISTS test_table")

    def test_health_endpoint(self):
        with TestClient(app) as client:
            response = client.get("/admin/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_update_rejects_non_main_branch(self):
        with TestClient(app) as client:
            original = app.state.config.copy()
            app.state.config = {**original, "admin_password": "secret"}
            try:
                cookie_value = create_session_cookie("secret")
                client.cookies.set(COOKIE_NAME, cookie_value)
                response = client.post("/admin/update")
                assert response.status_code == 400
                assert "error" in response.json()
            finally:
                app.state.config = original
