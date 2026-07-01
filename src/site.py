from __future__ import annotations

import shutil
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import database
from .api_client import build_provider
from .configuration import Settings
from .daily_message import should_generate_daily_message, utc_now, write_daily_message
from .odds import build_odds_provider
from .presentation import build_daily_message_context, build_dashboard_view
from .standings import build_effective_standings

BASE_DIR = Path(__file__).resolve().parent.parent


def build_static_site(
    settings: Settings,
    *,
    output_dir: Path | None = None,
    site_base_path: str = "",
    force_daily_report: bool = False,
    now: datetime | None = None,
) -> Path:
    run_time = now or utc_now()
    connection = refresh_site_data(settings)
    view = build_dashboard_view_from_database(
        settings,
        connection,
        site_base_path=site_base_path,
        now=run_time,
    )

    target_dir = output_dir or settings.site_output
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BASE_DIR / "static", target_dir / "static", dirs_exist_ok=True)
    (target_dir / ".nojekyll").write_text("", encoding="utf-8")
    (target_dir / "leaderboard").mkdir(parents=True, exist_ok=True)
    (target_dir / "draw").mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(BASE_DIR / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    home_html = env.get_template("index.html").render(
        view=view,
        asset_prefix="./static",
        home_href="./",
        leaderboard_href="./leaderboard/",
        draw_href="./draw/",
    )
    leaderboard_html = env.get_template("leaderboard.html").render(
        view=view,
        asset_prefix="../static",
        home_href="../",
        leaderboard_href="./",
        draw_href="../draw/",
    )
    draw_html = env.get_template("draw.html").render(
        view=view,
        asset_prefix="../static",
        home_href="../",
        leaderboard_href="../leaderboard/",
        draw_href="./",
    )
    (target_dir / "index.html").write_text(home_html, encoding="utf-8")
    (target_dir / "leaderboard" / "index.html").write_text(leaderboard_html, encoding="utf-8")
    (target_dir / "draw" / "index.html").write_text(draw_html, encoding="utf-8")

    maybe_generate_daily_message(settings, connection, view, run_time, force=force_daily_report)
    return target_dir


def refresh_site_data(settings: Settings) -> sqlite3.Connection:
    connection = database.connect(settings.database_path)
    database.migrate(connection)
    database.import_participants(connection, settings.participants_csv)

    provider = build_provider(settings)
    matches = provider.fetch_played_matches()
    completed_matches = [match for match in matches if provider.is_completed_status(match.status)]
    database.upsert_matches(connection, matches)
    database.replace_team_standings(connection, build_effective_standings(completed_matches, provider.fetch_standings()))
    return connection


def build_dashboard_view_from_database(
    settings: Settings,
    connection: sqlite3.Connection,
    *,
    site_base_path: str = "",
    now: datetime | None = None,
):
    odds_provider = build_odds_provider(settings)
    return build_dashboard_view(
        settings=settings,
        leaderboard_inputs=[dict(row) for row in database.fetch_leaderboard_inputs(connection)],
        standings_rows=[dict(row) for row in database.fetch_team_standings(connection)],
        matches_rows=[dict(row) for row in database.fetch_all_matches(connection)],
        odds_by_team=odds_provider.fetch_tournament_winner_odds(),
        site_base_path=site_base_path,
        now=now or datetime.now(UTC),
    )


def maybe_generate_daily_message(
    settings: Settings,
    connection: sqlite3.Connection,
    view,
    run_time: datetime,
    *,
    force: bool = False,
) -> Path | None:
    timezone_name = settings.raw.get("app", {}).get("timezone", "Europe/London")
    last_generated = database.get_job_state(connection, "daily_message:last_generated_date")
    should_generate = should_generate_daily_message(
        now=run_time,
        timezone_name=timezone_name,
        last_generated_for_date=last_generated,
        target_hour=settings.daily_message_hour,
    )
    if not force and not should_generate:
        return None

    context = build_daily_message_context(view)
    public_base_url = str(settings.raw.get("app", {}).get("public_base_url", "")).rstrip("/")
    if public_base_url:
        context = replace(context, leaderboard_url=f"{public_base_url}{view.leaderboard_href}")
    output_path = write_daily_message(
        output_dir=settings.daily_messages_output,
        run_time=run_time,
        timezone_name=timezone_name,
        context=context,
    )
    database.set_job_state(
        connection,
        "daily_message:last_generated_date",
        run_time.astimezone(ZoneInfo(timezone_name)).date().isoformat(),
    )
    return output_path
