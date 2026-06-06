import os
import hashlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import load_config, load_secrets
from src.database import Database
from src.i18n import load_global_i18n
from src.template import resolve_all_config_vars
from src.plugins import setup_card, render_card, init_plugins_schemas

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR.parent / "cache"


def _dev_reload_filter(record):
    return "/dev-reload" not in record.getMessage()


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(application):
    handler = logging.StreamHandler()
    handler.setFormatter(uvicorn.logging.DefaultFormatter("%(levelprefix)s %(message)s", use_colors=True))
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)

    db = Database()
    db.delete()
    db = Database()
    application.state.database = db
    application.state.config = load_config()
    application.state.secrets = load_secrets()

    language = application.state.config.get("language", "en")
    if isinstance(language, str) and "-" in language:
        language = language.split("-")[0]
    application.state.i18n = load_global_i18n(language)

    if os.environ.get("DEVELOPMENT"):
        logging.getLogger("uvicorn.access").addFilter(_dev_reload_filter)

    init_plugins_schemas(db)

    if not scheduler.running:
        scheduler.start()

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
    application.state.plugin_instances = plugin_instances

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
            "content": render_card(card, instances),
            "css_class": f"{card['plugin']}-card" if card.get("plugin") else "",
        }
        for card in cards
    ]


@app.get("/")
def index(request: Request):
    config = app.state.config
    secrets = app.state.secrets
    resolved_config = resolve_all_config_vars(config, secrets)
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


if __name__ == "__main__":
    import sys

    port = 8000
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])
    elif os.environ.get("PORT"):
        port = int(os.environ["PORT"])

    is_dev = os.environ.get("DEVELOPMENT") is not None
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=is_dev,
        reload_includes=["*.yml", "*.yaml"] if is_dev else None,
    )
