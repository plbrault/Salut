import os
import hashlib
import json
import logging
import socket
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import parse_qs

import uvicorn
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import ConfigError, load_config, load_secrets, validate_config
from src.database import Database
from src.i18n import load_global_i18n
from src.template import resolve_all_config_vars
from src.plugins import setup_card, render_card, init_plugins_schemas
from src.admin import (
    COOKIE_NAME, COOKIE_MAX_AGE,
    is_admin_enabled, check_admin_auth,
    create_session_cookie, get_admin_password, get_admin_error_message,
    admin_required, log_buffer, BufferHandler,
)

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR.parent / "cache"


def _dev_reload_filter(record):
    return "/dev-reload" not in record.getMessage()


def _get_last_commit():
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h %s"],
            capture_output=True, text=True, check=True, cwd=BASE_DIR.parent
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Unknown"


scheduler = BackgroundScheduler(job_defaults={"misfire_grace_time": None})


def reload_app_state():
    db = app.state.database
    try:
        app.state.config = load_config()
    except ConfigError as e:
        app.state.config_error = e.message
        app.state.config = {}
        app.state.secrets = {}
        app.state.i18n = {}
        app.state.plugin_instances = {}
        return

    app.state.config_error = None
    app.state.secrets = load_secrets()

    language = app.state.config.get("language", "en")
    if isinstance(language, str) and "-" in language:
        language = language.split("-")[0]
    app.state.i18n = load_global_i18n(language)

    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)

    init_plugins_schemas(db)

    resolved_config = resolve_all_config_vars(
        app.state.config, app.state.secrets, app.state.i18n
    )
    app.state.config = resolved_config

    plugin_instances = {}
    for card in app.state.config.get("cards", []):
        plugin_name = card.get("plugin")
        if plugin_name:
            instance = setup_card(card, db, scheduler, language)
            if instance is not None and plugin_name not in plugin_instances:
                plugin_instances[plugin_name] = instance
    app.state.plugin_instances = plugin_instances


@asynccontextmanager
async def lifespan(application):
    handler = logging.StreamHandler()
    handler.setFormatter(uvicorn.logging.DefaultFormatter("%(levelprefix)s %(message)s", use_colors=True))
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)

    buffer_handler = BufferHandler()
    logging.root.addHandler(buffer_handler)

    db = Database()
    db.delete()
    db = Database()
    application.state.database = db
    application.state.config_error = None

    if os.environ.get("DEVELOPMENT"):
        logging.getLogger("uvicorn.access").addFilter(_dev_reload_filter)

    if not scheduler.running:
        scheduler.start()

    reload_app_state()

    yield


app = FastAPI(title="Salut", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/cache", StaticFiles(directory=CACHE_DIR), name="cache")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _render_cards(cards):
    instances = app.state.plugin_instances
    return [
        {
            "title": card.get("title", ""),
            "colspan": card.get("colspan", 1),
            "column": card.get("column"),
            "content": render_card(card, instances),
            "css_class": f"{card['plugin']}-card" if card.get("plugin") else "",
        }
        for card in cards
    ]


@app.get("/")
def index(request: Request):
    if app.state.config_error:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": app.state.config_error},
        )

    app_config = app.state.config
    secrets = app.state.secrets
    resolved_config = resolve_all_config_vars(app_config, secrets)
    page_title = resolved_config.get("page_title", "")
    page_header = resolved_config.get("page_header", "")

    cards_data = _render_cards(resolved_config.get("cards", []))

    plugin_style_rules = ""
    for name, instance in app.state.plugin_instances.items():
        rules = getattr(type(instance), "card_style_rules", lambda: {})()
        for selector, declarations in rules.items():
            plugin_style_rules += f".{name}-card {selector} {{ {declarations} }}\n"

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "config": resolved_config,
            "page_title": page_title,
            "page_header": page_header,
            "favicon": resolved_config.get("favicon"),
            "language": resolved_config.get("language", "en-US"),
            "dev_mode": os.environ.get("DEVELOPMENT") is not None,
            "cards": cards_data,
            "max_cols": resolved_config.get("columns", 3),
            "plugin_style_rules": plugin_style_rules,
        },
    )


@app.get("/dev-reload")
def dev_reload(response: Response):
    h = hashlib.md5()
    for pattern in ["*.yml", "*.yaml"]:
        for path in sorted(BASE_DIR.parent.glob(pattern)):
            h.update(str(path.stat().st_mtime).encode())
    for path in sorted((BASE_DIR / "templates").rglob("*.html")):
        h.update(str(path.stat().st_mtime).encode())
    response.headers["x-reload"] = h.hexdigest()
    return {"version": h.hexdigest()}


@app.get("/admin/health")
def admin_health():
    return {"status": "ok"}


@app.get("/admin/login")
def admin_login_page(request: Request):
    if not is_admin_enabled(request):
        msg = get_admin_error_message(request)
        return HTMLResponse(
            "<html><head><title>Admin Not Enabled</title></head>"
            "<body style='font-family:sans-serif;text-align:center;padding:4rem;'>"
            "<h1>Admin Not Enabled</h1>"
            f"<p>{msg}</p>"
            "</body></html>",
            status_code=403,
        )
    if check_admin_auth(request):
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse(request, "admin.html", {"show_login": True, "error": None})


@app.post("/admin/login")
async def admin_login(request: Request):
    if not is_admin_enabled(request):
        msg = get_admin_error_message(request)
        return HTMLResponse(
            "<html><head><title>Admin Not Enabled</title></head>"
            "<body style='font-family:sans-serif;text-align:center;padding:4rem;'>"
            "<h1>Admin Not Enabled</h1>"
            f"<p>{msg}</p>"
            "</body></html>",
            status_code=403,
        )
    body = await request.json()
    password = body.get("password", "")
    if password == get_admin_password(request):
        response = RedirectResponse("/admin", status_code=302)
        cookie_value = create_session_cookie(password)
        response.set_cookie(COOKIE_NAME, cookie_value, max_age=COOKIE_MAX_AGE, httponly=True)
        return response
    return templates.TemplateResponse(request, "admin.html", {"show_login": True, "error": "Invalid password"})


@app.post("/admin/logout")
async def admin_logout(request: Request):
    if not is_admin_enabled(request):
        msg = get_admin_error_message(request)
        return HTMLResponse(
            "<html><head><title>Admin Not Enabled</title></head>"
            "<body style='font-family:sans-serif;text-align:center;padding:4rem;'>"
            "<h1>Admin Not Enabled</h1>"
            f"<p>{msg}</p>"
            "</body></html>",
            status_code=403,
        )
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


@app.get("/admin")
@admin_required
def admin_page(request: Request, reloaded: bool = False):
    config_path = BASE_DIR.parent / "config.yml"
    config_content = ""
    config_exists = config_path.exists()
    if config_exists:
        config_content = config_path.read_text(encoding="utf-8")
    return templates.TemplateResponse(request, "admin.html", {
        "show_login": False,
        "config_content": config_content,
        "config_exists": config_exists,
        "last_commit": _get_last_commit(),
        "reloaded": reloaded,
    })


@app.get("/admin/logs")
@admin_required
def admin_logs(request: Request):  # pylint: disable=unused-argument
    return list(log_buffer)


@app.put("/admin/config")
@admin_required
async def admin_save_config(request: Request):
    raw = await request.body()
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = json.loads(raw)
    else:
        body = parse_qs(raw.decode()) if raw else {}
        body = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in body.items()}
    content = body.get("content", "")
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return HTMLResponse(f'<span style="color:#dc2626;">YAML syntax error: {e}</span>')
    try:
        validate_config(parsed, "config.yml")
    except ConfigError as e:
        return HTMLResponse(f'<span style="color:#dc2626;">{e.message}</span>')
    config_path = BASE_DIR.parent / "config.yml"
    config_path.write_text(content, encoding="utf-8")
    reload_app_state()
    return HTMLResponse('<span style="color:#16a34a;">Config saved and reloaded successfully</span>')


@app.post("/admin/validate")
@admin_required
async def admin_validate_config(request: Request):
    raw = await request.body()
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = json.loads(raw)
    else:
        body = parse_qs(raw.decode()) if raw else {}
        body = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in body.items()}
    content = body.get("content", "")
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return HTMLResponse(f'<span style="color:#dc2626;">YAML syntax error: {e}</span>')
    try:
        validate_config(parsed, "config.yml")
    except ConfigError as e:
        return HTMLResponse(f'<span style="color:#dc2626;">{e.message}</span>')
    return HTMLResponse('<span style="color:#16a34a;">Config is valid</span>')


@app.post("/admin/reload")
@admin_required
def admin_reload(request: Request):  # pylint: disable=unused-argument
    try:
        reload_app_state()
        return HTMLResponse('<span style="color:#16a34a;">Config reloaded successfully</span>')
    except Exception as e:  # pylint: disable=broad-except
        return HTMLResponse(f'<span style="color:#dc2626;">{e}</span>')


@app.post("/admin/restart")
@admin_required
def admin_restart(request: Request):  # pylint: disable=unused-argument,inconsistent-return-statements
    invocation_id = os.environ.get("INVOCATION_ID")
    if invocation_id:
        subprocess.Popen(["systemctl", "--user", "restart", "salut"])  # pylint: disable=consider-using-with
        return {"status": "restarting"}
    python_path = sys.executable
    os.execv(python_path, [python_path, "-m", "src.main"])


@app.post("/admin/update")
@admin_required
def admin_update(request: Request):  # pylint: disable=unused-argument,inconsistent-return-statements
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False)
    if result.stdout.strip():
        return JSONResponse({"error": "Uncommitted changes. Please commit or stash before updating."}, status_code=400)
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=False)
    branch = result.stdout.strip()
    result = subprocess.run(["git", "pull", "origin", branch], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return JSONResponse({"error": f"Git pull failed: {result.stderr}"}, status_code=500)
    subprocess.run(["pipenv", "install"], capture_output=True, check=False)
    invocation_id = os.environ.get("INVOCATION_ID")
    if invocation_id:
        subprocess.Popen(["systemctl", "--user", "restart", "salut"])  # pylint: disable=consider-using-with
        return {"status": "updating"}
    python_path = sys.executable
    os.execv(python_path, [python_path, "-m", "src.main"])


@app.post("/admin/check-update")
@admin_required
def admin_check_update(request: Request):  # pylint: disable=unused-argument
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False)
    if result.stdout.strip():
        return JSONResponse({"error": "Uncommitted changes. Please commit or stash before updating."}, status_code=400)
    result = subprocess.run(["git", "fetch", "--quiet"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return JSONResponse({"error": f"Git fetch failed: {result.stderr}"}, status_code=500)
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=False)
    branch = result.stdout.strip()
    local = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    remote = subprocess.run(
        ["git", "rev-parse", f"origin/{branch}"], capture_output=True, text=True, check=False
    ).stdout.strip()
    if local == remote:
        return {"has_update": False}
    commit_info = subprocess.run(
        ["git", "log", "-1", "--format=%h %s", f"origin/{branch}"],
        capture_output=True, text=True, check=False
    ).stdout.strip()
    return {"has_update": True, "commit": commit_info}


if __name__ == "__main__":
    port = 8000
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])
    elif os.environ.get("PORT"):
        port = int(os.environ["PORT"])

    is_dev = os.environ.get("DEVELOPMENT") is not None

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.set_inheritable(False)
    sock.bind(("0.0.0.0", port))
    sock.listen(5)

    config = uvicorn.Config(
        "src.main:app",
        reload=is_dev,
        reload_includes=["*.yml", "*.yaml"] if is_dev else None,
    )
    server = uvicorn.Server(config)
    server.run(sockets=[sock])
