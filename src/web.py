from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from . import database
from .configuration import load_settings
from .site import build_dashboard_view_from_database

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="World Cup Sweepstake")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    settings = load_settings(BASE_DIR)
    connection = database.connect(settings.database_path)
    database.migrate(connection)
    view = build_dashboard_view_from_database(settings, connection, site_base_path="")
    return TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "view": view,
            "asset_prefix": "/static",
            "home_href": "/",
            "leaderboard_href": "/leaderboard/",
        },
    )


@app.get("/leaderboard", response_class=HTMLResponse)
@app.get("/leaderboard/", response_class=HTMLResponse)
def leaderboard(request: Request) -> HTMLResponse:
    settings = load_settings(BASE_DIR)
    connection = database.connect(settings.database_path)
    database.migrate(connection)
    view = build_dashboard_view_from_database(settings, connection, site_base_path="")
    return TEMPLATES.TemplateResponse(
        "leaderboard.html",
        {
            "request": request,
            "view": view,
            "asset_prefix": "/static",
            "home_href": "/",
            "leaderboard_href": "/leaderboard/",
        },
    )
