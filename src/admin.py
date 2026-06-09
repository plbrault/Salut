import hashlib
import hmac
import logging
import secrets
from collections import deque
from datetime import datetime
from functools import wraps

from fastapi import Request
from fastapi.responses import RedirectResponse

COOKIE_NAME = "salut_admin_session"
COOKIE_MAX_AGE = 86400 * 7

_session_secret = secrets.token_hex(32)


def _sign(data):
    return hmac.new(
        _session_secret.encode(), data.encode(), hashlib.sha256
    ).hexdigest()


def create_session_cookie(password):
    sig = _sign(password)
    return f"{password}|{sig}"


def verify_session_cookie(cookie_value):
    if not cookie_value:
        return False
    parts = cookie_value.split("|", 1)
    if len(parts) != 2:
        return False
    payload, sig = parts
    expected = _sign(payload)
    return hmac.compare_digest(sig, expected)


def get_admin_password(request):
    config = request.app.state.config
    return config.get("admin_password")


def get_admin_error_message(request):
    config = request.app.state.config
    password = config.get("admin_password")
    if password:
        return None
    if "admin_password" in config:
        return (
            "Set a value for <code>admin_password</code> in <code>secrets.yml</code>"
            " and restart the server to enable the admin page."
        )
    return (
        "Set <code>admin_password</code> in your config"
        " and restart the server to enable the admin page."
    )


def is_admin_enabled(request):
    return bool(get_admin_password(request))


def check_admin_auth(request):
    password = get_admin_password(request)
    if not password:
        return False
    cookie = request.cookies.get(COOKIE_NAME)
    return verify_session_cookie(cookie)


def admin_required(handler):
    @wraps(handler)
    async def wrapper(request: Request, *args, **kwargs):
        if not is_admin_enabled(request):
            from fastapi.responses import HTMLResponse
            msg = get_admin_error_message(request)
            return HTMLResponse(
                "<html><head><title>Admin Not Enabled</title></head>"
                "<body style='font-family:sans-serif;text-align:center;padding:4rem;'>"
                "<h1>Admin Not Enabled</h1>"
                f"<p>{msg}</p>"
                "</body></html>",
                status_code=403,
            )
        if not check_admin_auth(request):
            return RedirectResponse("/admin/login", status_code=302)
        result = handler(request, *args, **kwargs)
        if hasattr(result, "__await__"):
            return await result
        return result
    return wrapper


log_buffer = deque(maxlen=500)


class BufferHandler(logging.Handler):
    def emit(self, record):
        try:
            ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
            log_buffer.append({
                "timestamp": ts,
                "level": record.levelname,
                "message": record.getMessage(),
            })
        except Exception:  # pylint: disable=broad-except
            pass
