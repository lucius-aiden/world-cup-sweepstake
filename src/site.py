from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import database
from .api_client import build_provider
from .configuration import Settings
from .presentation import build_dashboard_view

BASE_DIR = Path(__file__).resolve().parent.parent


def build_static_site(settings: Settings) -> Path:
    connection = database.connect(settings.database_path)
    database.migrate(connection)
    database.import_participants(connection, settings.participants_csv)

    provider = build_provider(settings)
    matches = provider.fetch_recent_matches()
    completed_matches = [match for match in matches if provider.is_completed_status(match.status)]
    database.upsert_matches(connection, completed_matches)
    database.replace_team_standings(connection, provider.fetch_standings())

    leaderboard_inputs = [dict(row) for row in database.fetch_leaderboard_inputs(connection)]
    latest_match = database.fetch_latest_completed_match(connection)
    view = build_dashboard_view(
        settings=settings,
        leaderboard_inputs=leaderboard_inputs,
        latest_match_row=dict(latest_match) if latest_match else None,
    )

    output_dir = settings.site_output
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BASE_DIR / "static", output_dir / "static", dirs_exist_ok=True)
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    env = Environment(
        loader=FileSystemLoader(str(BASE_DIR / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html = env.get_template("index.html").render(view=view, asset_prefix="./static")
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    return output_dir
