from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class DailyMessageContext:
    current_leader: str
    best_performing_teams: list[str]
    teams_in_trouble: list[str]
    biggest_team_changes: list[str]
    todays_key_fixtures: list[str]
    leaderboard_url: str


def should_generate_daily_message(
    *,
    now: datetime,
    timezone_name: str,
    last_generated_for_date: str | None,
    target_hour: int = 7,
) -> bool:
    local_now = now.astimezone(ZoneInfo(timezone_name))
    if local_now.weekday() >= 5:
        return False
    if local_now.hour != target_hour or local_now.minute >= 15:
        return False
    return local_now.date().isoformat() != last_generated_for_date


def write_daily_message(
    *,
    output_dir: Path,
    run_time: datetime,
    timezone_name: str,
    context: DailyMessageContext,
) -> Path:
    local_date = run_time.astimezone(ZoneInfo(timezone_name)).date().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{local_date}.txt"
    lines = [
        f"Current leader: {context.current_leader}",
        f"Best performing teams: {', '.join(context.best_performing_teams) if context.best_performing_teams else 'None yet'}",
        f"Teams in trouble: {', '.join(context.teams_in_trouble) if context.teams_in_trouble else 'None'}",
        f"Biggest team changes: {', '.join(context.biggest_team_changes) if context.biggest_team_changes else 'No major swings'}",
        f"Today's key fixtures: {', '.join(context.todays_key_fixtures) if context.todays_key_fixtures else 'No fixtures today'}",
        f"Full leaderboard: {context.leaderboard_url}",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def utc_now() -> datetime:
    return datetime.now(UTC)
