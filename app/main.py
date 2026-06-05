from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.config import load_config
from app.database import init_database

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Salut")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def startup():
    init_database()
    app.state.config = load_config()


@app.get("/")
def index(request: Request):
    config = app.state.config
    return templates.TemplateResponse(
        request,
        "index.html",
        {"config": config},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
