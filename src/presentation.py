from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .leaderboard import build_leaderboard
from .models import LeaderboardRow

FLAG_OVERRIDES = {
    "ALG": "🇩🇿",
    "ARG": "🇦🇷",
    "AUS": "🇦🇺",
    "AUT": "🇦🇹",
    "BEL": "🇧🇪",
    "BIH": "🇧🇦",
    "BRA": "🇧🇷",
    "CAN": "🇨🇦",
    "COD": "🇨🇩",
    "COL": "🇨🇴",
    "CPV": "🇨🇻",
    "CIV": "🇨🇮",
    "CRO": "🇭🇷",
    "CUW": "🇨🇼",
    "CZE": "🇨🇿",
    "ECU": "🇪🇨",
    "EGY": "🇪🇬",
    "ENG": "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "ESP": "🇪🇸",
    "FRA": "🇫🇷",
    "GER": "🇩🇪",
    "GHA": "🇬🇭",
    "HTI": "🇭🇹",
    "IRN": "🇮🇷",
    "IRQ": "🇮🇶",
    "JOR": "🇯🇴",
    "JPN": "🇯🇵",
    "KOR": "🇰🇷",
    "KSA": "🇸🇦",
    "MAR": "🇲🇦",
    "MEX": "🇲🇽",
    "NED": "🇳🇱",
    "NOR": "🇳🇴",
    "NZL": "🇳🇿",
    "PAN": "🇵🇦",
    "PAR": "🇵🇾",
    "POR": "🇵🇹",
    "QAT": "🇶🇦",
    "RSA": "🇿🇦",
    "SCO": "🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    "SEN": "🇸🇳",
    "SUI": "🇨🇭",
    "SWE": "🇸🇪",
    "TUN": "🇹🇳",
    "TUR": "🇹🇷",
    "URU": "🇺🇾",
    "USA": "🇺🇸",
    "UZB": "🇺🇿",
}


@dataclass(frozen=True)
class TeamCell:
    name: str
    code: str
    flag: str
    points: int
    alive: bool


@dataclass(frozen=True)
class ParticipantRowView:
    rank: int
    player: str
    team_1: TeamCell
    team_2: TeamCell
    total_points: int
    teams_alive: int


@dataclass(frozen=True)
class MatchView:
    summary: str
    stage: str | None
    played_at: str


@dataclass(frozen=True)
class DashboardView:
    tournament_name: str
    generated_at: str
    leaderboard: list[LeaderboardRow]
    table_rows: list[ParticipantRowView]
    podium: list[LeaderboardRow]
    latest_match: MatchView | None


def build_dashboard_view(
    settings: Any,
    leaderboard_inputs: list[dict],
    latest_match_row: dict | None = None,
) -> DashboardView:
    leaderboard, _ = build_leaderboard(leaderboard_inputs, previous_ranks={})
    index_by_player = {row.player: row for row in leaderboard}

    grouped: dict[str, list[dict]] = {}
    for item in leaderboard_inputs:
        grouped.setdefault(item["player"], []).append(item)

    table_rows: list[ParticipantRowView] = []
    for player, teams in grouped.items():
        ranked_row = index_by_player[player]
        ordered = sorted(teams, key=lambda item: int(item.get("team_slot", 0)))
        first, second = (_team_cell(ordered[0]), _team_cell(ordered[1]))
        table_rows.append(
            ParticipantRowView(
                rank=ranked_row.rank,
                player=player,
                team_1=first,
                team_2=second,
                total_points=ranked_row.total_points,
                teams_alive=ranked_row.teams_alive,
            )
        )

    table_rows.sort(key=lambda row: (row.rank, row.player.lower()))

    latest_match = None
    if latest_match_row:
        latest_match = MatchView(
            summary=f'{latest_match_row["home_team"]} {latest_match_row["home_score"]}-{latest_match_row["away_score"]} {latest_match_row["away_team"]}',
            stage=latest_match_row["stage"],
            played_at=_format_match_time(latest_match_row["match_date"]),
        )

    return DashboardView(
        tournament_name=settings.raw["tournament"]["name"],
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        leaderboard=leaderboard,
        table_rows=table_rows,
        podium=leaderboard[:3],
        latest_match=latest_match,
    )


def _team_cell(team: dict) -> TeamCell:
    code = str(team["team_code"])
    return TeamCell(
        name=str(team["team_name"]),
        code=code,
        flag=FLAG_OVERRIDES.get(code, "🏳️"),
        points=int(team["points"]),
        alive=bool(team["alive"]),
    )


def _format_match_time(raw: str) -> str:
    try:
        return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return raw
