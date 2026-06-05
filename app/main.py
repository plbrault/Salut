from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import load_config
from app.database import init_database
from app.template import resolve_config_vars

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Salut")
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def startup():
    init_database()
    app.state.config = load_config()


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
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
