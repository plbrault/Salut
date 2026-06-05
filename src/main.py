import os
import hashlib
import logging
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import load_config
from src.database import init_database
from src.template import resolve_config_vars

BASE_DIR = Path(__file__).resolve().parent


def _dev_reload_filter(record):
    return "/dev-reload" not in record.getMessage()


app = FastAPI(title="Salut")
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def startup():
    init_database()
    app.state.config = load_config()
    if os.environ.get("DEVELOPMENT"):
        logging.getLogger("uvicorn.access").addFilter(_dev_reload_filter)


@app.get("/")
def index(request: Request):
    config = app.state.config
    page_title = resolve_config_vars(config.get("page_title", ""), config)
    page_header = resolve_config_vars(config.get("page_header", ""), config)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "config": config,
            "page_title": page_title,
            "page_header": page_header,
            "language": config.get("language", "en-US"),
            "dev_mode": os.environ.get("DEVELOPMENT") is not None,
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
    import uvicorn

    port = 8000
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1])

    is_dev = os.environ.get("DEVELOPMENT") is not None
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=is_dev,
        reload_includes=["*.yml", "*.yaml"] if is_dev else None,
    )
