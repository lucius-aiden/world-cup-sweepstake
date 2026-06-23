from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from . import database
from .configuration import load_settings
from .presentation import build_dashboard_view

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="World Cup Sweepstake")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    settings = load_settings(BASE_DIR)
    connection = database.connect(settings.database_path)
    database.migrate(connection)
    database.import_participants(connection, settings.participants_csv)
    leaderboard_inputs = [dict(row) for row in database.fetch_leaderboard_inputs(connection)]
    latest_match = database.fetch_latest_completed_match(connection)
    view = build_dashboard_view(
        settings=settings,
        leaderboard_inputs=leaderboard_inputs,
        latest_match_row=dict(latest_match) if latest_match else None,
    )
    return TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "view": view,
            "asset_prefix": "/static",
        },
    )
