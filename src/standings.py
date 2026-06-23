from __future__ import annotations

from .models import Match, TeamStanding
from .team_codes import resolve_team_code


def build_effective_standings(
    matches: list[Match],
    provider_standings: list[TeamStanding],
) -> list[TeamStanding]:
    standings_by_code = {standing.team_code: standing for standing in provider_standings}
    computed: dict[str, TeamStanding] = {}

    for match in matches:
        if not _is_group_stage(match):
            continue
        if match.home_score is None or match.away_score is None:
            continue

        home_code = resolve_team_code(match.home_team, match.home_team_code)
        away_code = resolve_team_code(match.away_team, match.away_team_code)
        home = _current_standing(computed, standings_by_code, home_code, match.home_team)
        away = _current_standing(computed, standings_by_code, away_code, match.away_team)

        home_points, away_points = _match_points(match.home_score, match.away_score)
        computed[home_code] = TeamStanding(
            team_code=home.team_code,
            team_name=home.team_name,
            played=home.played + 1,
            won=home.won + int(home_points == 3),
            drawn=home.drawn + int(home_points == 1),
            lost=home.lost + int(home_points == 0),
            goals_for=home.goals_for + match.home_score,
            goals_against=home.goals_against + match.away_score,
            goal_difference=(home.goals_for + match.home_score) - (home.goals_against + match.away_score),
            points=home.points + home_points,
            alive=_alive_for(home, standings_by_code.get(home_code)),
        )
        computed[away_code] = TeamStanding(
            team_code=away.team_code,
            team_name=away.team_name,
            played=away.played + 1,
            won=away.won + int(away_points == 3),
            drawn=away.drawn + int(away_points == 1),
            lost=away.lost + int(away_points == 0),
            goals_for=away.goals_for + match.away_score,
            goals_against=away.goals_against + match.home_score,
            goal_difference=(away.goals_for + match.away_score) - (away.goals_against + match.home_score),
            points=away.points + away_points,
            alive=_alive_for(away, standings_by_code.get(away_code)),
        )

    merged = standings_by_code.copy()
    merged.update(computed)
    return sorted(merged.values(), key=lambda item: item.team_name)


def _current_standing(
    computed: dict[str, TeamStanding],
    standings_by_code: dict[str, TeamStanding],
    team_code: str,
    team_name: str,
) -> TeamStanding:
    existing = computed.get(team_code)
    if existing:
        return existing
    provider = standings_by_code.get(team_code)
    if provider:
        return TeamStanding(
            team_code=provider.team_code,
            team_name=provider.team_name,
            played=0,
            won=0,
            drawn=0,
            lost=0,
            goals_for=0,
            goals_against=0,
            goal_difference=0,
            points=0,
            alive=provider.alive,
        )
    return TeamStanding(
        team_code=team_code,
        team_name=team_name,
        played=0,
        won=0,
        drawn=0,
        lost=0,
        goals_for=0,
        goals_against=0,
        goal_difference=0,
        points=0,
        alive=True,
    )


def _alive_for(current: TeamStanding, provider: TeamStanding | None) -> bool:
    if provider is not None:
        return provider.alive
    return current.alive


def _is_group_stage(match: Match) -> bool:
    stage = (match.stage or "").upper()
    return "GROUP" in stage or "FIRST_STAGE" in stage or "FIRSTSTAGE" in stage


def _match_points(home_score: int, away_score: int) -> tuple[int, int]:
    if home_score > away_score:
        return 3, 0
    if home_score < away_score:
        return 0, 3
    return 1, 1
