from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from .daily_message import DailyMessageContext
from .leaderboard import build_leaderboard
from .models import TeamOdds

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
COMPLETED_STATUSES = {"FINISHED", "FT", "AET", "PEN"}


@dataclass(frozen=True)
class StatusView:
    label: str
    tone: str


@dataclass(frozen=True)
class MatchSummaryView:
    title: str
    detail: str


@dataclass(frozen=True)
class TeamCardView:
    flag: str
    team_name: str
    group_label: str
    group_points: int
    form: list[str]
    status: StatusView
    last_match: MatchSummaryView | None
    next_match: MatchSummaryView | None
    win_odds: str | None


@dataclass(frozen=True)
class ParticipantRowView:
    rank: int
    player: str
    total_points: int
    teams_alive: int
    team_1: TeamCardView
    team_2: TeamCardView


@dataclass(frozen=True)
class InsightItemView:
    title: str
    detail: str
    tone: str = "neutral"


@dataclass(frozen=True)
class InsightSectionView:
    title: str
    items: list[InsightItemView]
    empty_message: str


@dataclass(frozen=True)
class DashboardView:
    tournament_name: str
    generated_at: str
    last_updated: str
    participants_count: int
    leaderboard_count: int
    latest_result: str
    home_href: str
    leaderboard_href: str
    asset_prefix: str
    leaderboard_rows: list[ParticipantRowView]
    insight_sections: list[InsightSectionView]


def build_dashboard_view(
    *,
    settings: Any,
    leaderboard_inputs: list[dict],
    standings_rows: list[dict] | None = None,
    matches_rows: list[dict] | None = None,
    odds_by_team: dict[str, TeamOdds] | None = None,
    site_base_path: str = "",
    now: datetime | None = None,
) -> DashboardView:
    timezone_name = settings.raw.get("app", {}).get("timezone", "Europe/London")
    display_zone = ZoneInfo(timezone_name)
    generated_at = now or datetime.now(UTC)
    leaderboard, _ = build_leaderboard(leaderboard_inputs, previous_ranks={})
    standings_rows = standings_rows or []
    matches_rows = matches_rows or []
    odds_by_team = odds_by_team or {}

    standings_by_code = {str(row["team_code"]): dict(row) for row in standings_rows}
    matches_by_code = _group_matches_by_team(matches_rows)
    group_context_by_code = _build_group_context(matches_rows)
    grouped_inputs: dict[str, list[dict[str, Any]]] = {}
    for item in leaderboard_inputs:
        grouped_inputs.setdefault(str(item["player"]), []).append(dict(item))

    leaderboard_rows: list[ParticipantRowView] = []
    for row in leaderboard:
        teams = sorted(grouped_inputs[row.player], key=lambda item: int(item.get("team_slot", 0)))
        first = _build_team_card(teams[0], standings_by_code, group_context_by_code, matches_by_code, odds_by_team, display_zone)
        second = _build_team_card(teams[1], standings_by_code, group_context_by_code, matches_by_code, odds_by_team, display_zone)
        leaderboard_rows.append(
            ParticipantRowView(
                rank=row.rank,
                player=row.player,
                total_points=row.total_points,
                teams_alive=row.teams_alive,
                team_1=first,
                team_2=second,
            )
        )

    latest_completed = [match for match in matches_rows if _is_completed(match)]
    latest_completed.sort(key=lambda match: str(match["match_date"]), reverse=True)
    latest_result = "No completed matches yet"
    if latest_completed:
        latest_result = _match_scoreline(latest_completed[0])

    insight_sections = _build_insight_sections(matches_rows, standings_rows, group_context_by_code, display_zone, generated_at)
    base_path = _normalize_base_path(site_base_path)
    return DashboardView(
        tournament_name=settings.raw["tournament"]["name"],
        generated_at=generated_at.astimezone(display_zone).strftime("%Y-%m-%d %H:%M %Z"),
        last_updated=generated_at.astimezone(display_zone).strftime("%A %d %b %Y, %H:%M %Z"),
        participants_count=len(leaderboard_rows),
        leaderboard_count=len(leaderboard_rows),
        latest_result=latest_result,
        home_href=_join_path(base_path, "/"),
        leaderboard_href=_join_path(base_path, "leaderboard/"),
        asset_prefix=_join_path(base_path, "static"),
        leaderboard_rows=leaderboard_rows,
        insight_sections=insight_sections,
    )


def determine_team_status(standing: dict[str, Any] | None) -> StatusView:
    if not standing:
        return StatusView(label="Alive", tone="alive")
    qualification = str(standing.get("qualification_status") or "").lower()
    alive = bool(standing.get("alive", 1))
    group_position = _normalized_group_position(standing)
    played = _safe_int(standing.get("played")) or 0

    if not alive or "eliminated" in qualification:
        return StatusView(label="Eliminated", tone="eliminated")
    if any(keyword in qualification for keyword in ("qualified", "advance")):
        return StatusView(label="Qualified", tone="qualified")
    if group_position is not None and played >= 3 and group_position <= 2:
        return StatusView(label="Qualified", tone="qualified")
    if group_position is not None and group_position > 2 and played >= 2:
        return StatusView(label="At Risk", tone="risk")
    return StatusView(label="Alive", tone="alive")


def build_daily_message_context(view: DashboardView) -> DailyMessageContext:
    section_map = {section.title: section for section in view.insight_sections}
    leader = view.leaderboard_rows[0] if view.leaderboard_rows else None
    current_leader = "No leader yet"
    if leader:
        current_leader = f"{leader.player} ({leader.total_points} pts)"
    return DailyMessageContext(
        current_leader=current_leader,
        best_performing_teams=[item.title for item in section_map.get("Best Performing Teams", _empty_section("")).items[:3]],
        teams_in_trouble=[item.title for item in section_map.get("Teams In Trouble", _empty_section("")).items[:3]],
        biggest_team_changes=[item.title for item in section_map.get("Biggest Winners Today", _empty_section("")).items[:3]],
        todays_key_fixtures=[item.title for item in section_map.get("Today's Key Fixtures", _empty_section("")).items[:3]],
        leaderboard_url=view.leaderboard_href,
    )


def _build_team_card(
    team_input: dict[str, Any],
    standings_by_code: dict[str, dict[str, Any]],
    group_context_by_code: dict[str, dict[str, Any]],
    matches_by_code: dict[str, list[dict[str, Any]]],
    odds_by_team: dict[str, TeamOdds],
    display_zone: ZoneInfo,
) -> TeamCardView:
    team_code = str(team_input["team_code"])
    standing = standings_by_code.get(team_code)
    context = group_context_by_code.get(team_code, {})
    team_matches = matches_by_code.get(team_code, [])
    last_match = _last_match(team_matches, display_zone)
    next_match = _next_match(team_matches, display_zone)
    odds = odds_by_team.get(team_code)
    return TeamCardView(
        flag=FLAG_OVERRIDES.get(team_code, "🏳️"),
        team_name=str(team_input["team_name"]),
        group_label=_group_label(context or standing),
        group_points=int(standing["points"]) if standing else int(team_input.get("points", 0)),
        form=_team_form(team_matches, team_code),
        status=determine_team_status((standing | context | {"alive": team_input.get("alive", 1)}) if standing or context else {"alive": team_input.get("alive", 1)}),
        last_match=last_match,
        next_match=next_match,
        win_odds=_format_odds(odds),
    )


def _build_insight_sections(
    matches_rows: list[dict[str, Any]],
    standings_rows: list[dict[str, Any]],
    group_context_by_code: dict[str, dict[str, Any]],
    display_zone: ZoneInfo,
    generated_at: datetime,
) -> list[InsightSectionView]:
    standings = [dict(row) for row in standings_rows]
    standings = [row | group_context_by_code.get(str(row["team_code"]), {}) for row in standings]
    now_local = generated_at.astimezone(display_zone)
    today = now_local.date()
    completed_today = [
        match for match in matches_rows if _is_completed(match) and _parse_match_date(match["match_date"]).astimezone(display_zone).date() == today
    ]
    upcoming_today = [
        match for match in matches_rows if not _is_completed(match) and _parse_match_date(match["match_date"]).astimezone(display_zone).date() == today
    ]
    latest_results = sorted(
        [match for match in matches_rows if _is_completed(match)],
        key=lambda match: str(match["match_date"]),
        reverse=True,
    )[:5]

    best_performing = sorted(
        standings,
        key=lambda row: (-int(row["points"]), -int(row["goal_difference"]), str(row["team_name"]).lower()),
    )[:5]
    teams_in_trouble = [
        row for row in standings if determine_team_status(row).label in {"At Risk", "Eliminated"}
    ][:5]
    biggest_winners = sorted(
        [match for match in completed_today if _goal_margin(match) > 0],
        key=lambda match: (-_goal_margin(match), str(match["match_date"])),
    )[:5]

    return [
        InsightSectionView(
            title="Top Matches",
            items=[
                InsightItemView(
                    title=_winning_team(match),
                    detail=_match_scoreline(match),
                    tone="qualified",
                )
                for match in biggest_winners
            ],
            empty_message="No completed wins today yet.",
        ),
        InsightSectionView(
            title="Today's Key Fixtures",
            items=[
                InsightItemView(
                    title=f'{match["home_team"]} vs {match["away_team"]}',
                    detail=_match_time(match, display_zone),
                )
                for match in sorted(upcoming_today, key=lambda match: str(match["match_date"]))[:5]
            ],
            empty_message="No fixtures scheduled today.",
        ),
        InsightSectionView(
            title="Best Performing Teams",
            items=[
                InsightItemView(
                    title=str(row["team_name"]),
                    detail=f'{_group_label(row)} · {int(row["points"])} pts · GD {int(row["goal_difference"]):+d}',
                    tone="qualified",
                )
                for row in best_performing
            ],
            empty_message="No standings available yet.",
        ),
        InsightSectionView(
            title="Teams In Trouble",
            items=[
                InsightItemView(
                    title=str(row["team_name"]),
                    detail=f'{_group_label(row)} · {int(row["points"])} pts · {determine_team_status(row).label}',
                    tone=determine_team_status(row).tone,
                )
                for row in teams_in_trouble
            ],
            empty_message="No teams are in trouble right now.",
        ),
        InsightSectionView(
            title="Latest Results",
            items=[
                InsightItemView(
                    title=_match_scoreline(match),
                    detail=_match_meta(match, display_zone),
                )
                for match in latest_results
            ],
            empty_message="Waiting for the first result.",
        ),
    ]


def _last_match(matches: list[dict[str, Any]], display_zone: ZoneInfo) -> MatchSummaryView | None:
    completed = [match for match in matches if _is_completed(match)]
    if not completed:
        return None
    latest = max(completed, key=lambda match: str(match["match_date"]))
    return MatchSummaryView(title=_match_scoreline(latest), detail=_match_meta(latest, display_zone))


def _next_match(matches: list[dict[str, Any]], display_zone: ZoneInfo) -> MatchSummaryView | None:
    upcoming = [match for match in matches if not _is_completed(match)]
    if not upcoming:
        return None
    next_match = min(upcoming, key=lambda match: str(match["match_date"]))
    return MatchSummaryView(
        title=f'{next_match["home_team"]} vs {next_match["away_team"]}',
        detail=_match_time(next_match, display_zone),
    )


def _team_form(matches: list[dict[str, Any]], team_code: str) -> list[str]:
    completed = sorted(
        [match for match in matches if _is_completed(match)],
        key=lambda match: str(match["match_date"]),
        reverse=True,
    )[:5]
    return [_result_for_team(match, team_code) for match in completed]


def _result_for_team(match: dict[str, Any], team_code: str) -> str:
    home_score = _safe_int(match.get("home_score"))
    away_score = _safe_int(match.get("away_score"))
    if home_score is None or away_score is None:
        return "D"
    if home_score == away_score:
        return "D"
    is_home = str(match.get("home_team_code") or "") == team_code
    team_won = home_score > away_score if is_home else away_score > home_score
    return "W" if team_won else "L"


def _group_matches_by_team(matches_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in matches_rows:
        match = dict(row)
        home_code = match.get("home_team_code")
        away_code = match.get("away_team_code")
        if home_code:
            grouped.setdefault(str(home_code), []).append(match)
        if away_code:
            grouped.setdefault(str(away_code), []).append(match)
    return grouped


def _group_label(standing: dict[str, Any] | None) -> str:
    if not standing:
        return "Group position TBD"
    group_name = standing.get("group_name")
    group_position = _normalized_group_position(standing)
    if not group_name or group_position is None:
        return "Group position TBD"
    return f"{group_name} · {group_position}{_ordinal(int(group_position))}"


def _build_group_context(matches_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for row in matches_rows:
        match = dict(row)
        if str(match.get("stage") or "").upper() != "GROUP_STAGE":
            continue
        group_name = match.get("group_name")
        if not group_name:
            continue
        home_code = str(match.get("home_team_code") or "")
        away_code = str(match.get("away_team_code") or "")
        home_name = str(match.get("home_team") or "")
        away_name = str(match.get("away_team") or "")
        if home_code:
            groups.setdefault(group_name, {}).setdefault(home_code, _group_row(home_code, home_name, group_name))
        if away_code:
            groups.setdefault(group_name, {}).setdefault(away_code, _group_row(away_code, away_name, group_name))
        if not _is_completed(match):
            continue
        home_score = _safe_int(match.get("home_score"))
        away_score = _safe_int(match.get("away_score"))
        if home_score is None or away_score is None or not home_code or not away_code:
            continue
        home = groups[group_name][home_code]
        away = groups[group_name][away_code]
        home["played"] += 1
        away["played"] += 1
        home["goals_for"] += home_score
        home["goals_against"] += away_score
        away["goals_for"] += away_score
        away["goals_against"] += home_score
        if home_score > away_score:
            home["won"] += 1
            away["lost"] += 1
            home["points"] += 3
        elif home_score < away_score:
            away["won"] += 1
            home["lost"] += 1
            away["points"] += 3
        else:
            home["drawn"] += 1
            away["drawn"] += 1
            home["points"] += 1
            away["points"] += 1

    by_team: dict[str, dict[str, Any]] = {}
    for group_name, teams in groups.items():
        ordered = sorted(
            teams.values(),
            key=lambda row: (-row["points"], -(row["goals_for"] - row["goals_against"]), -row["goals_for"], row["team_name"].lower()),
        )
        for index, row in enumerate(ordered, start=1):
            by_team[row["team_code"]] = {
                "group_name": _format_group_name(group_name),
                "group_position": index,
            }
    return by_team


def _group_row(team_code: str, team_name: str, group_name: str) -> dict[str, Any]:
    return {
        "team_code": team_code,
        "team_name": team_name,
        "group_name": group_name,
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "goals_for": 0,
        "goals_against": 0,
        "points": 0,
    }


def _format_group_name(raw: str) -> str:
    cleaned = str(raw).replace("GROUP_", "Group ").replace("_", " ").title()
    return cleaned


def _normalized_group_position(standing: dict[str, Any] | None) -> int | None:
    if not standing:
        return None
    position = _safe_int(standing.get("group_position"))
    if position is None or position < 1 or position > 4:
        return None
    return position


def _ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")


def _match_scoreline(match: dict[str, Any]) -> str:
    return f'{match["home_team"]} {_safe_int(match.get("home_score"))}-{_safe_int(match.get("away_score"))} {match["away_team"]}'


def _match_meta(match: dict[str, Any], display_zone: ZoneInfo) -> str:
    stage = str(match.get("stage") or "Match")
    return f"{stage.replace('_', ' ').title()} · {_match_time(match, display_zone)}"


def _match_time(match: dict[str, Any], display_zone: ZoneInfo) -> str:
    return _parse_match_date(match["match_date"]).astimezone(display_zone).strftime("%d %b %H:%M %Z")


def _parse_match_date(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _format_odds(odds: TeamOdds | None) -> str | None:
    if odds is None:
        return None
    return f"{odds.decimal:.2f}"


def _goal_margin(match: dict[str, Any]) -> int:
    home_score = _safe_int(match.get("home_score")) or 0
    away_score = _safe_int(match.get("away_score")) or 0
    return abs(home_score - away_score)


def _winning_team(match: dict[str, Any]) -> str:
    home_score = _safe_int(match.get("home_score")) or 0
    away_score = _safe_int(match.get("away_score")) or 0
    if home_score >= away_score:
        return str(match["home_team"])
    return str(match["away_team"])


def _is_completed(match: dict[str, Any]) -> bool:
    return str(match.get("status", "")).upper() in COMPLETED_STATUSES


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _join_path(base_path: str, suffix: str) -> str:
    base = _normalize_base_path(base_path)
    if suffix in {"", "/"}:
        return f"{base}/" if base != "/" else "/"
    cleaned = suffix.lstrip("/")
    if base == "/":
        return f"/{cleaned}"
    return f"{base}/{cleaned}".replace("//", "/")


def _normalize_base_path(base_path: str) -> str:
    cleaned = (base_path or "").strip()
    if not cleaned or cleaned == "/":
        return "/"
    return "/" + cleaned.strip("/")


def _empty_section(title: str) -> InsightSectionView:
    return InsightSectionView(title=title, items=[], empty_message="")
