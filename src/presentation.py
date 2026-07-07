from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .daily_message import DailyMessageContext
from .leaderboard_state import (
    KnockoutContext,
    alive_flag as _alive_flag,
    build_knockout_context as _build_knockout_context,
    effective_alive as _effective_alive,
    enrich_leaderboard_inputs as _enrich_leaderboard_inputs,
    is_knockout_stage as _is_knockout_stage,
    knockout_phase_active as _knockout_phase_active,
    next_stage_label as _next_stage_label,
    normalized_group_position as _normalized_group_position,
    stage_bonus as _stage_bonus,
    winner_code as _winner_code,
)
from .leaderboard import build_leaderboard
from .match_format import format_match_scoreline
from .models import TeamOdds, TopScorer
from .team_codes import resolve_team_code

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
    top_scorer: str | None
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
class DrawTeamView:
    flag: str
    team_name: str
    owner_label: str | None
    source_label: str | None
    eliminated: bool
    won: bool
    placeholder: bool


@dataclass(frozen=True)
class DrawMatchView:
    stage_label: str
    detail: str
    row_start: int
    source_gap: int
    round_index: int
    placeholder: bool
    home_team: DrawTeamView
    away_team: DrawTeamView


@dataclass(frozen=True)
class DrawRoundView:
    title: str
    matches: list[DrawMatchView]


@dataclass(frozen=True)
class InsightItemView:
    title: str
    detail: str
    tone: str = "neutral"


@dataclass(frozen=True)
class InsightSectionView:
    title: str
    description: str
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
    leaderboard_blurb: str
    home_href: str
    leaderboard_href: str
    draw_href: str
    asset_prefix: str
    leaderboard_rows: list[ParticipantRowView]
    draw_rounds: list[DrawRoundView]
    draw_grid_rows: int
    insight_sections: list[InsightSectionView]


def build_dashboard_view(
    *,
    settings: Any,
    leaderboard_inputs: list[dict],
    standings_rows: list[dict] | None = None,
    matches_rows: list[dict] | None = None,
    top_scorers: list[TopScorer] | None = None,
    odds_by_team: dict[str, TeamOdds] | None = None,
    site_base_path: str = "",
    now: datetime | None = None,
) -> DashboardView:
    timezone_name = settings.raw.get("app", {}).get("timezone", "Europe/London")
    display_zone = ZoneInfo(timezone_name)
    generated_at = now or datetime.now(UTC)
    standings_rows = [_normalize_standing_row(dict(row)) for row in (standings_rows or [])]
    matches_rows = [_normalize_match_row(dict(row)) for row in (matches_rows or [])]
    odds_by_team = odds_by_team or {}

    standings_by_code = {str(row["team_code"]): dict(row) for row in standings_rows}
    matches_by_code = _group_matches_by_team(matches_rows)
    group_context_by_code = _build_group_context(matches_rows)
    team_owners = _build_team_owner_map(leaderboard_inputs)
    top_scorers = top_scorers or []
    top_scorers_by_team = _build_top_scorer_map(top_scorers)
    knockout_active = _knockout_phase_active(matches_rows)
    knockout_context_by_code = _build_knockout_context(
        matches_by_code,
        standings_by_code,
        knockout_active,
    )
    enriched_inputs = _enrich_leaderboard_inputs(
        leaderboard_inputs,
        standings_rows,
        matches_rows,
    )
    leaderboard, _ = build_leaderboard(enriched_inputs, previous_ranks={})
    grouped_inputs: dict[str, list[dict[str, Any]]] = {}
    for item in enriched_inputs:
        grouped_inputs.setdefault(str(item["player"]), []).append(dict(item))

    leaderboard_rows: list[ParticipantRowView] = []
    for row in leaderboard:
        teams = sorted(grouped_inputs[row.player], key=lambda item: int(item.get("team_slot", 0)))
        first = _build_team_card(
            teams[0],
            standings_by_code,
            group_context_by_code,
            matches_by_code,
            knockout_context_by_code,
            odds_by_team,
            top_scorers_by_team,
            display_zone,
            knockout_active,
        )
        second = _build_team_card(
            teams[1],
            standings_by_code,
            group_context_by_code,
            matches_by_code,
            knockout_context_by_code,
            odds_by_team,
            top_scorers_by_team,
            display_zone,
            knockout_active,
        )
        leaderboard_rows.append(
            ParticipantRowView(
                rank=row.rank,
                player=row.player,
                total_points=row.total_points,
                teams_alive=int(_status_counts_as_alive(first.status)) + int(_status_counts_as_alive(second.status)),
                team_1=first,
                team_2=second,
            )
        )
    leaderboard_rows = _rank_participant_rows(leaderboard_rows)
    draw_rounds = _build_draw_rounds(
        matches_rows,
        standings_by_code,
        group_context_by_code,
        knockout_context_by_code,
        team_owners,
        display_zone,
        knockout_active=knockout_active,
    )

    latest_completed = [match for match in matches_rows if _is_completed(match)]
    latest_completed.sort(key=lambda match: str(match["match_date"]), reverse=True)
    latest_result = "No completed matches yet"
    if latest_completed:
        latest_result = _match_scoreline(latest_completed[0])

    insight_sections = _build_insight_sections(
        matches_rows,
        standings_rows,
        top_scorers,
        group_context_by_code,
        team_owners,
        knockout_context_by_code,
        display_zone,
        generated_at,
        fixture_day_ends_hour=getattr(settings, "fixture_day_ends_hour", 5),
        knockout_active=knockout_active,
    )
    base_path = _normalize_base_path(site_base_path)
    return DashboardView(
        tournament_name=settings.raw["tournament"]["name"],
        generated_at=generated_at.astimezone(display_zone).strftime("%Y-%m-%d %H:%M %Z"),
        last_updated=generated_at.astimezone(display_zone).strftime("%A %d %b %Y, %H:%M %Z"),
        participants_count=len(leaderboard_rows),
        leaderboard_count=len(leaderboard_rows),
        latest_result=latest_result,
        leaderboard_blurb=_leaderboard_blurb(),
        home_href=_join_path(base_path, "/"),
        leaderboard_href=_join_path(base_path, "leaderboard/"),
        draw_href=_join_path(base_path, "draw/"),
        asset_prefix=_join_path(base_path, "static"),
        leaderboard_rows=leaderboard_rows,
        draw_rounds=draw_rounds,
        draw_grid_rows=_draw_grid_rows(draw_rounds),
        insight_sections=insight_sections,
    )


def _normalize_standing_row(row: dict[str, Any]) -> dict[str, Any]:
    row["team_code"] = resolve_team_code(str(row.get("team_name") or ""), row.get("team_code"))
    return row


def _normalize_match_row(row: dict[str, Any]) -> dict[str, Any]:
    row["home_team_code"] = resolve_team_code(str(row.get("home_team") or ""), row.get("home_team_code"))
    row["away_team_code"] = resolve_team_code(str(row.get("away_team") or ""), row.get("away_team_code"))
    return row


def determine_team_status(standing: dict[str, Any] | None) -> StatusView:
    if not standing:
        return StatusView(label="Alive", tone="alive")
    qualification = str(standing.get("qualification_status") or "").lower()
    alive = _alive_flag(standing.get("alive", 1))
    group_position = _normalized_group_position(standing)
    played = _safe_int(standing.get("played")) or 0
    if standing.get("knockout_phase"):
        return StatusView(label="Qualified", tone="qualified") if alive else StatusView(label="Eliminated", tone="eliminated")
    if standing.get("knockout_active") and group_position is not None and played >= 3 and group_position > 2:
        return StatusView(label="Eliminated", tone="eliminated")

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
        teams_in_trouble=[
            item.title
            for item in (
                section_map.get("Teams In Trouble")
                or section_map.get("Latest Knockouts")
                or _empty_section("")
            ).items[:3]
        ],
        biggest_team_changes=[item.title for item in section_map.get("Top Matches", _empty_section("")).items[:3]],
        todays_key_fixtures=[item.title for item in section_map.get("Today's Key Fixtures", _empty_section("")).items[:3]],
        leaderboard_url=view.leaderboard_href,
    )


def _build_team_card(
    team_input: dict[str, Any],
    standings_by_code: dict[str, dict[str, Any]],
    group_context_by_code: dict[str, dict[str, Any]],
    matches_by_code: dict[str, list[dict[str, Any]]],
    knockout_context_by_code: dict[str, KnockoutContext],
    odds_by_team: dict[str, TeamOdds],
    top_scorers_by_team: dict[str, TopScorer],
    display_zone: ZoneInfo,
    knockout_active: bool,
) -> TeamCardView:
    team_code = str(team_input["team_code"])
    standing = standings_by_code.get(team_code)
    context = group_context_by_code.get(team_code, {})
    knockout_context = knockout_context_by_code.get(team_code)
    team_matches = matches_by_code.get(team_code, [])
    odds = odds_by_team.get(team_code)
    status_context = {}
    if standing:
        status_context |= standing
    if context:
        status_context |= context
    status_context["alive"] = _effective_alive(
        fallback=team_input.get("alive", 1),
        standing=standing,
        knockout_context=knockout_context,
        knockout_active=knockout_active,
    )
    status_context["knockout_phase"] = knockout_active and knockout_context is not None
    status_context["knockout_active"] = knockout_active
    status = determine_team_status(status_context)
    last_match = _last_match(team_matches, display_zone)
    next_match = None if status.label == "Eliminated" else _next_match(team_matches, display_zone)
    return TeamCardView(
        flag=FLAG_OVERRIDES.get(team_code, "🏳️"),
        team_name=str(team_input["team_name"]),
        group_label=_group_label(context or standing, knockout_context=knockout_context),
        group_points=int(standing["points"]) if standing else int(team_input.get("points", 0)),
        form=_team_form(team_matches, team_code),
        status=status,
        last_match=last_match,
        next_match=next_match,
        top_scorer=_format_team_top_scorer(top_scorers_by_team.get(team_code)),
        win_odds=_format_odds(odds),
    )


def _build_top_scorer_map(top_scorers: list[TopScorer]) -> dict[str, TopScorer]:
    best_by_team: dict[str, TopScorer] = {}
    for scorer in top_scorers:
        current = best_by_team.get(scorer.team_code)
        if current is None or (
            scorer.goals,
            scorer.assists,
            scorer.penalties,
            scorer.player_name.lower(),
        ) > (
            current.goals,
            current.assists,
            current.penalties,
            current.player_name.lower(),
        ):
            best_by_team[scorer.team_code] = scorer
    return best_by_team


def _format_team_top_scorer(scorer: TopScorer | None) -> str | None:
    if scorer is None:
        return None
    return f"{scorer.player_name} ({scorer.goals} goals)"


def _build_insight_sections(
    matches_rows: list[dict[str, Any]],
    standings_rows: list[dict[str, Any]],
    top_scorers: list[TopScorer],
    group_context_by_code: dict[str, dict[str, Any]],
    team_owners: dict[str, list[str]],
    knockout_context_by_code: dict[str, KnockoutContext],
    display_zone: ZoneInfo,
    generated_at: datetime,
    *,
    fixture_day_ends_hour: int,
    knockout_active: bool,
) -> list[InsightSectionView]:
    standings = [dict(row) for row in standings_rows]
    standings = [row | group_context_by_code.get(str(row["team_code"]), {}) for row in standings]
    now_local = generated_at.astimezone(display_zone)
    fixture_window_start, fixture_window_end = _fixture_day_window(now_local, fixture_day_ends_hour)
    recent_window_start = (now_local - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    completed_recent = [
        match
        for match in matches_rows
        if _is_completed(match) and _parse_match_date(match["match_date"]).astimezone(display_zone) >= recent_window_start
    ]
    upcoming_today = [
        match
        for match in matches_rows
        if not _is_completed(match)
        and fixture_window_start <= _parse_match_date(match["match_date"]).astimezone(display_zone) < fixture_window_end
    ]
    latest_results = sorted(
        [match for match in matches_rows if _is_completed(match)],
        key=lambda match: str(match["match_date"]),
        reverse=True,
    )
    latest_knockouts: list[InsightItemView] = []

    if knockout_active:
        best_performing = sorted(
            [
                row
                for row in standings
                if _effective_alive(
                    fallback=row.get("alive", 1),
                    standing=row,
                    knockout_context=knockout_context_by_code.get(str(row.get("team_code") or "")),
                    knockout_active=knockout_active,
                )
            ],
            key=lambda row: (
                -knockout_context_by_code.get(str(row["team_code"]), KnockoutContext(None, 0)).advancement_bonus,
                -int(row["points"]),
                -int(row["goal_difference"]),
                str(row["team_name"]).lower(),
            ),
        )[:5]
        latest_knockouts = _latest_knockouts(
            matches_rows,
            standings_rows,
            team_owners,
            knockout_context_by_code,
            display_zone,
        )[:5]
        teams_in_trouble = sorted(
            [row for row in standings if determine_team_status(row).label in {"At Risk", "Eliminated"}],
            key=lambda row: (
                int(row["points"]),
                int(row["goal_difference"]),
                int(row.get("goals_for", 0)),
                str(row["team_name"]).lower(),
            ),
        )[:5]
    else:
        best_performing = sorted(
            standings,
            key=lambda row: (-int(row["points"]), -int(row["goal_difference"]), str(row["team_name"]).lower()),
        )[:5]
        teams_in_trouble = sorted(
            [row for row in standings if determine_team_status(row).label in {"At Risk", "Eliminated"}],
            key=lambda row: (
                int(row["points"]),
                int(row["goal_difference"]),
                int(row.get("goals_for", 0)),
                str(row["team_name"]).lower(),
            ),
        )[:5]
    latest_results_limit = max(1, len(latest_knockouts)) if latest_knockouts else 5
    top_match_count = len(upcoming_today) if upcoming_today else 3
    biggest_winners = sorted(
        [match for match in completed_recent if _goal_margin(match) > 0],
        key=lambda match: (-_total_goals(match), -_goal_margin(match), str(match["match_date"])),
    )[:top_match_count]

    return [
        InsightSectionView(
            title="Top Matches",
            description="Top matches are the biggest scoring games or result swings from the last two days.",
            items=[
                InsightItemView(
                    title=f'{_flag_for_match_team(match)} {_winning_team(match)}',
                    detail=_match_scoreline(match),
                    tone="qualified",
                )
                for match in biggest_winners
            ],
            empty_message="No standout completed matches in the last two days.",
        ),
        InsightSectionView(
            title="Today's Key Fixtures",
            description=f"Key fixtures run from {fixture_window_start.strftime('%H:%M %Z')} today through before {fixture_window_end.strftime('%H:%M %Z')} tomorrow, ordered by kickoff time.",
            items=[
                InsightItemView(
                    title=f'{_flag_for_code(match.get("home_team_code"))} {match["home_team"]} vs {_flag_for_code(match.get("away_team_code"))} {match["away_team"]}',
                    detail=_match_time(match, display_zone),
                )
                for match in sorted(upcoming_today, key=lambda match: str(match["match_date"]))[:5]
            ],
            empty_message="No fixtures scheduled today.",
        ),
        InsightSectionView(
            title="Top Scorers",
            description="Top scorers come straight from the current competition scorer feed, including assists and penalties.",
            items=[
                InsightItemView(
                    title=f'{_flag_for_code(scorer.team_code)} {scorer.player_name}',
                    detail=(
                        f'{scorer.team_name} {_owner_suffix(team_owners, scorer.team_code)} · '
                        f'{scorer.goals} goals · {scorer.assists} assists'
                        + (f' · {scorer.penalties} pens' if scorer.penalties else "")
                    ),
                )
                for scorer in top_scorers[:5]
            ],
            empty_message="Top scorer data is not available yet.",
        ),
        InsightSectionView(
            title="Best Performing Teams",
            description=(
                "Best performing teams are ranked by deepest secured knockout stage, then group points, then goal difference."
                if knockout_active
                else "Best performing teams are ranked by group points, then goal difference, then goals scored."
            ),
            items=[
                InsightItemView(
                    title=f'{_flag_for_code(row.get("team_code"))} {row["team_name"]} {_owner_suffix(team_owners, row.get("team_code"))}',
                    detail=(
                        f'{knockout_context_by_code.get(str(row["team_code"]), KnockoutContext("Knockout stage", 0)).stage_label or "Knockout stage"} · {int(row["points"])} pts · GD {int(row["goal_difference"]):+d}'
                        if knockout_active
                        else f'{_group_label(row)} · {int(row["points"])} pts · GD {int(row["goal_difference"]):+d}'
                    ),
                    tone="qualified",
                )
                for row in best_performing
            ],
            empty_message="No standings available yet.",
        ),
        InsightSectionView(
            title="Latest Knockouts" if latest_knockouts else "Teams In Trouble",
            description=(
                "Latest knockouts show the most recent teams eliminated from the tournament."
                if latest_knockouts
                else "Teams in trouble are the bottom sides in each group, ordered by the fewest points then the worst goal difference."
            ),
            items=(
                latest_knockouts
                if latest_knockouts
                else [
                    InsightItemView(
                        title=f'{_flag_for_code(row.get("team_code"))} {row["team_name"]} {_owner_suffix(team_owners, row.get("team_code"))}',
                        detail=f'{_group_label(row)} · {int(row["points"])} pts · GD {int(row["goal_difference"]):+d}',
                        tone=determine_team_status(row).tone,
                    )
                    for row in teams_in_trouble
                ]
            ),
            empty_message="No teams were knocked out recently." if latest_knockouts else "No teams are in trouble right now.",
        ),
        InsightSectionView(
            title="Latest Results",
            description="Latest results show the most recent completed matches, trimmed to keep pace with the knockout view.",
            items=[
                InsightItemView(
                    title=_match_scoreline(match),
                    detail=_match_meta(match, display_zone),
                )
                for match in latest_results[:latest_results_limit]
            ],
            empty_message="Waiting for the first result.",
        ),
    ]


def _build_draw_rounds(
    matches_rows: list[dict[str, Any]],
    standings_by_code: dict[str, dict[str, Any]],
    group_context_by_code: dict[str, dict[str, Any]],
    knockout_context_by_code: dict[str, KnockoutContext],
    team_owners: dict[str, list[str]],
    display_zone: ZoneInfo,
    *,
    knockout_active: bool,
) -> list[DrawRoundView]:
    matches_by_stage: dict[str, list[dict[str, Any]]] = {
        stage_key: sorted(
            [
                dict(match)
                for match in matches_rows
                if _draw_stage_key(match.get("stage")) == stage_key
            ],
            key=lambda match: str(match["match_date"]),
        )
        for stage_key, _ in _draw_stage_order()
    }
    present_stage_indexes = [
        index
        for index, (stage_key, _) in enumerate(_draw_stage_order())
        if matches_by_stage.get(stage_key)
    ]
    if not present_stage_indexes:
        return []

    first_stage_index = min(present_stage_indexes)
    previous_count = len(matches_by_stage[_draw_stage_order()[first_stage_index][0]])
    rounds: list[DrawRoundView] = []
    for absolute_index, (stage_key, stage_title) in enumerate(_draw_stage_order()[first_stage_index:], start=first_stage_index):
        stage_matches = matches_by_stage[stage_key]
        expected_count = max(len(stage_matches), previous_count)
        relative_round_index = absolute_index - first_stage_index
        match_views: list[DrawMatchView] = []
        for slot_index in range(expected_count):
            match = stage_matches[slot_index] if slot_index < len(stage_matches) else None
            match_views.append(
                _build_draw_match(
                    match,
                    stage_title=stage_title,
                    stage_key=stage_key,
                    slot_index=slot_index,
                    round_index=relative_round_index,
                    display_zone=display_zone,
                    standings_by_code=standings_by_code,
                    group_context_by_code=group_context_by_code,
                    knockout_context_by_code=knockout_context_by_code,
                    team_owners=team_owners,
                    knockout_active=knockout_active,
                )
            )
        previous_count = max(1, (expected_count + 1) // 2)
        rounds.append(
            DrawRoundView(
                title=stage_title,
                matches=match_views,
            )
        )
    return rounds


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


def _group_label(standing: dict[str, Any] | None, *, knockout_context: KnockoutContext | None = None) -> str:
    if knockout_context and knockout_context.stage_label:
        return knockout_context.stage_label
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


def _build_team_owner_map(leaderboard_inputs: list[dict[str, Any]]) -> dict[str, list[str]]:
    owners: dict[str, set[str]] = {}
    for item in leaderboard_inputs:
        code = str(item.get("team_code") or "")
        player = str(item.get("player") or "")
        if not code or not player:
            continue
        owners.setdefault(code, set()).add(player)
    return {code: sorted(players) for code, players in owners.items()}


def _owner_suffix(team_owners: dict[str, list[str]], team_code: Any) -> str:
    owners = team_owners.get(str(team_code or ""), [])
    label = ", ".join(owners) if owners else "Unassigned"
    return f"[{label}]"


def _owner_label(team_owners: dict[str, list[str]], team_code: Any) -> str | None:
    owners = team_owners.get(str(team_code or ""), [])
    if not owners:
        return None
    return ", ".join(owners)

def _fixture_day_window(now_local: datetime, fixture_day_ends_hour: int) -> tuple[datetime, datetime]:
    anchor = now_local.replace(hour=fixture_day_ends_hour, minute=0, second=0, microsecond=0)
    if now_local < anchor:
        anchor -= timedelta(days=1)
    return anchor, anchor + timedelta(days=1)

def _leaderboard_blurb() -> str:
    return (
        "Each participant has two teams. Group-stage matches score 3 points for a win, "
        "1 for a draw, and 0 for a loss. Once the knockout rounds begin, teams get a "
        "stage bonus that increases by round: 10 for the round of 32, 20 for the round of 16, "
        "30 for quarter-finals, 40 for semi-finals, and 50 for the champion. "
        "Rankings are based on total points, with teams still alive only used to break ties."
    )

def _latest_knockouts(
    matches_rows: list[dict[str, Any]],
    standings_rows: list[dict[str, Any]],
    team_owners: dict[str, list[str]],
    knockout_context_by_code: dict[str, KnockoutContext],
    display_zone: ZoneInfo,
) -> list[InsightItemView]:
    items: list[tuple[tuple[datetime, int, int, str], InsightItemView]] = []
    seen_codes: set[str] = set()
    for match in sorted(
        [row for row in matches_rows if _is_completed(row) and _is_knockout_stage(row.get("stage"))],
        key=lambda row: str(row["match_date"]),
        reverse=True,
    ):
        loser_code = _loser_code(match)
        loser_name = _loser_name(match)
        if not loser_code or not loser_name:
            continue
        if not team_owners.get(loser_code):
            continue
        seen_codes.add(loser_code)
        items.append(
            (
                (
                    _parse_match_date(match["match_date"]),
                    -1,
                    -1,
                    str(loser_name).lower(),
                ),
                InsightItemView(
                    title=f'{_flag_for_code(loser_code)} {loser_name} {_owner_suffix(team_owners, loser_code)}',
                    detail=f'{_stage_label(match.get("stage"))} · {_match_scoreline(match)} · {_match_time(match, display_zone)}',
                    tone="eliminated",
                ),
            )
        )

    matches_by_code = _group_matches_by_team(matches_rows)
    for standing in standings_rows:
        team_code = str(standing.get("team_code") or "")
        if not team_code or team_code in seen_codes:
            continue
        if not team_owners.get(team_code):
            continue
        if _effective_alive(
            fallback=standing.get("alive", 1),
            standing=standing,
            knockout_context=knockout_context_by_code.get(team_code),
            knockout_active=True,
        ):
            continue
        if knockout_context_by_code.get(team_code) is not None:
            continue
        team_name = str(standing.get("team_name") or team_code)
        team_matches = [match for match in matches_by_code.get(team_code, []) if _is_completed(match)]
        if team_matches:
            latest_match = max(team_matches, key=lambda match: str(match["match_date"]))
            eliminated_sort_key = (
                _parse_match_date(latest_match["match_date"]),
                _safe_int(standing.get("points")) or 0,
                -(_normalized_group_position(standing) or 99),
                team_name.lower(),
            )
            detail = f'{_group_label(standing)} · Eliminated after group stage · {_match_time(latest_match, display_zone)}'
        else:
            eliminated_sort_key = (
                datetime.min.replace(tzinfo=UTC),
                _safe_int(standing.get("points")) or 0,
                -(_normalized_group_position(standing) or 99),
                team_name.lower(),
            )
            detail = f'{_group_label(standing)} · Eliminated after group stage'
        items.append(
            (
                eliminated_sort_key,
                InsightItemView(
                    title=f'{_flag_for_code(team_code)} {team_name} {_owner_suffix(team_owners, team_code)}',
                    detail=detail,
                    tone="eliminated",
                ),
            )
        )
    items.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in items]


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


def _flag_for_code(code: Any) -> str:
    if not code:
        return "🏳️"
    return FLAG_OVERRIDES.get(str(code), "🏳️")


def _flag_for_match_team(match: dict[str, Any]) -> str:
    home_score = _safe_int(match.get("home_score")) or 0
    away_score = _safe_int(match.get("away_score")) or 0
    if home_score >= away_score:
        return _flag_for_code(match.get("home_team_code"))
    return _flag_for_code(match.get("away_team_code"))

def _stage_label(stage: Any) -> str:
    value = str(stage or "").upper()
    if "THIRD" in value:
        return "Third-place playoff"
    if "FINAL" in value and "SEMI" not in value and "QUARTER" not in value:
        return "Final"
    if "SEMI" in value:
        return "Semi-finals"
    if "QUARTER" in value:
        return "Quarter-finals"
    if "16" in value:
        return "Round of 16"
    if "32" in value or "PLAYOFF" in value:
        return "Round of 32"
    return value.replace("_", " ").title() if value else "Knockout stage"


def _draw_stage_key(stage: Any) -> str | None:
    value = str(stage or "").upper()
    if "32" in value or "PLAYOFF" in value:
        return "round_of_32"
    if "16" in value:
        return "round_of_16"
    if "QUARTER" in value:
        return "quarter_finals"
    if "SEMI" in value:
        return "semi_finals"
    if "FINAL" in value and "SEMI" not in value and "QUARTER" not in value and "THIRD" not in value:
        return "final"
    return None


def _draw_stage_order() -> list[tuple[str, str]]:
    return [
        ("round_of_32", "Round of 32"),
        ("round_of_16", "Round of 16"),
        ("quarter_finals", "Quarter-finals"),
        ("semi_finals", "Semi-finals"),
        ("final", "Final"),
    ]


def _draw_grid_rows(rounds: list[DrawRoundView]) -> int:
    if not rounds:
        return 0
    return max(1, (len(rounds[0].matches) * 2) - 1)

def _ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")


def _match_scoreline(match: dict[str, Any]) -> str:
    return format_match_scoreline(match)


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
    implied_probability = 1 / odds.decimal if odds.decimal else 0
    one_in = max(1, round(odds.decimal))
    return f"1 in {one_in} chance ({implied_probability:.1%})"


def _goal_margin(match: dict[str, Any]) -> int:
    home_score = _safe_int(match.get("home_score")) or 0
    away_score = _safe_int(match.get("away_score")) or 0
    return abs(home_score - away_score)


def _total_goals(match: dict[str, Any]) -> int:
    home_score = _safe_int(match.get("home_score")) or 0
    away_score = _safe_int(match.get("away_score")) or 0
    return home_score + away_score


def _winning_team(match: dict[str, Any]) -> str:
    home_score = _safe_int(match.get("home_score")) or 0
    away_score = _safe_int(match.get("away_score")) or 0
    if home_score >= away_score:
        return str(match["home_team"])
    return str(match["away_team"])

def _loser_code(match: dict[str, Any]) -> str | None:
    winner_code = _winner_code(match)
    home_code = str(match.get("home_team_code") or "")
    away_code = str(match.get("away_team_code") or "")
    if winner_code == home_code:
        return away_code
    if winner_code == away_code:
        return home_code
    return None


def _loser_name(match: dict[str, Any]) -> str | None:
    winner_code = _winner_code(match)
    home_code = str(match.get("home_team_code") or "")
    away_code = str(match.get("away_team_code") or "")
    if winner_code == home_code:
        return str(match.get("away_team") or "")
    if winner_code == away_code:
        return str(match.get("home_team") or "")
    return None


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
    return InsightSectionView(title=title, description="", items=[], empty_message="")


def _status_counts_as_alive(status: StatusView) -> bool:
    return status.label != "Eliminated"


def _rank_participant_rows(rows: list[ParticipantRowView]) -> list[ParticipantRowView]:
    ordered = sorted(
        rows,
        key=lambda row: (
            -row.total_points,
            -row.teams_alive,
            row.player.lower(),
        ),
    )
    return [
        ParticipantRowView(
            rank=index,
            player=row.player,
            total_points=row.total_points,
            teams_alive=row.teams_alive,
            team_1=row.team_1,
            team_2=row.team_2,
        )
        for index, row in enumerate(ordered, start=1)
    ]


def _build_draw_team(
    match: dict[str, Any] | None,
    *,
    side: str,
    standings_by_code: dict[str, dict[str, Any]],
    group_context_by_code: dict[str, dict[str, Any]],
    knockout_context_by_code: dict[str, KnockoutContext],
    team_owners: dict[str, list[str]],
    knockout_active: bool,
    source_label: str | None = None,
) -> DrawTeamView:
    if match is None:
        return DrawTeamView(
            flag="🏳️",
            team_name="TBD",
            owner_label=None,
            source_label=source_label,
            eliminated=False,
            won=False,
            placeholder=True,
        )
    team_key = f"{side}_team"
    code_key = f"{side}_team_code"
    team_name = str(match.get(team_key) or "TBD")
    team_code = str(match.get(code_key) or "")
    standing = standings_by_code.get(team_code)
    context = group_context_by_code.get(team_code, {})
    knockout_context = knockout_context_by_code.get(team_code)
    merged = {}
    if standing:
        merged |= standing
    if context:
        merged |= context
    merged["alive"] = _effective_alive(
        fallback=standing.get("alive", 1) if standing else 1,
        standing=standing,
        group_context=context,
        knockout_context=knockout_context,
        knockout_active=knockout_active,
    )
    merged["knockout_phase"] = knockout_active and knockout_context is not None
    merged["knockout_active"] = knockout_active
    status = determine_team_status(merged if (standing or context or knockout_context) else None)
    winner_code = _winner_code(match)
    return DrawTeamView(
        flag=_flag_for_code(team_code),
        team_name=team_name,
        owner_label=_owner_label(team_owners, team_code),
        source_label=source_label if not team_code else None,
        eliminated=status.label == "Eliminated",
        won=bool(team_code and winner_code and team_code == winner_code),
        placeholder=not bool(team_code),
    )


def _build_draw_match(
    match: dict[str, Any] | None,
    *,
    stage_title: str,
    stage_key: str,
    slot_index: int,
    round_index: int,
    display_zone: ZoneInfo,
    standings_by_code: dict[str, dict[str, Any]],
    group_context_by_code: dict[str, dict[str, Any]],
    knockout_context_by_code: dict[str, KnockoutContext],
    team_owners: dict[str, list[str]],
    knockout_active: bool,
) -> DrawMatchView:
    source_gap = 0 if round_index == 0 else 2 ** (round_index - 1)
    row_start = (2 ** round_index) + (slot_index * (2 ** (round_index + 1)))
    home_source = _draw_source_label(stage_key, slot_index, side="home")
    away_source = _draw_source_label(stage_key, slot_index, side="away")
    return DrawMatchView(
        stage_label=stage_title,
        detail=_match_meta(match, display_zone) if match else "Match TBD",
        row_start=row_start,
        source_gap=source_gap,
        round_index=round_index,
        placeholder=match is None,
        home_team=_build_draw_team(
            match,
            side="home",
            standings_by_code=standings_by_code,
            group_context_by_code=group_context_by_code,
            knockout_context_by_code=knockout_context_by_code,
            team_owners=team_owners,
            knockout_active=knockout_active,
            source_label=home_source,
        ),
        away_team=_build_draw_team(
            match,
            side="away",
            standings_by_code=standings_by_code,
            group_context_by_code=group_context_by_code,
            knockout_context_by_code=knockout_context_by_code,
            team_owners=team_owners,
            knockout_active=knockout_active,
            source_label=away_source,
        ),
    )


def _draw_source_label(stage_key: str, slot_index: int, *, side: str) -> str | None:
    order = [key for key, _ in _draw_stage_order()]
    if stage_key not in order:
        return None
    stage_index = order.index(stage_key)
    if stage_index == 0:
        return None
    previous_stage_key = order[stage_index - 1]
    previous_stage_short = _draw_stage_short(previous_stage_key)
    match_number = (slot_index * 2) + (1 if side == "home" else 2)
    return f"Winner {previous_stage_short} {match_number}"


def _draw_stage_short(stage_key: str) -> str:
    return {
        "round_of_32": "R32",
        "round_of_16": "R16",
        "quarter_finals": "QF",
        "semi_finals": "SF",
        "final": "F",
    }.get(stage_key, stage_key)
