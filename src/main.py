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

from src.config import load_config
from src import database
from src.template import resolve_config_vars
from src.plugins import setup_card, render_card

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

    database.init_database()
    application.state.config = load_config()
    if os.environ.get("DEVELOPMENT"):
        logging.getLogger("uvicorn.access").addFilter(_dev_reload_filter)

    if not scheduler.running:
        scheduler.start()

    plugin_instances = {}
    for card in app.state.config.get("cards", []):
        plugin_name = card.get("plugin")
        if plugin_name:
            instance = setup_card(card, database, scheduler)
            if instance is not None and plugin_name not in plugin_instances:
                plugin_instances[plugin_name] = instance
    application.state.plugin_instances = plugin_instances

    yield


app = FastAPI(title="Salut", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/cache", StaticFiles(directory=CACHE_DIR), name="cache")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _compute_grid_layout(num_cols, cards):
    cards_data = []
    current_col = 1
    current_row = 1

    for card in cards:
        colspan = card.get("colspan", 1)

        if current_col + colspan - 1 > num_cols:
            current_row += 1
            current_col = 1

        cards_data.append({
            "title": card.get("title", ""),
            "colspan": colspan,
            "col": current_col,
            "row": current_row,
            "content": render_card(card, app.state.plugin_instances),
        })

        current_col += colspan

    num_rows = current_row
    return cards_data, num_cols, num_rows


@app.get("/")
def index(request: Request):
    config = app.state.config
    page_title = resolve_config_vars(config.get("page_title", ""), config)
    page_header = resolve_config_vars(config.get("page_header", ""), config)

    cards_data, num_cols, num_rows = _compute_grid_layout(
        config.get("columns", 3),
        config.get("cards", []),
    )

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "config": config,
            "page_title": page_title,
            "page_header": page_header,
            "language": config.get("language", "en-US"),
            "dev_mode": os.environ.get("DEVELOPMENT") is not None,
            "cards": cards_data,
            "num_cols": num_cols,
            "num_rows": num_rows,
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
