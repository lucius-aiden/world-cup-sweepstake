from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .team_codes import resolve_team_code


@dataclass(frozen=True)
class KnockoutContext:
    stage_label: str | None
    advancement_bonus: int
    latest_elimination_match: dict[str, Any] | None = None
    is_active: bool = False


def enrich_leaderboard_inputs(
    leaderboard_inputs: list[dict[str, Any]],
    standings_rows: list[dict[str, Any]],
    matches_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    standings_by_code = {
        resolve_team_code(str(row.get("team_name") or ""), row.get("team_code")): dict(row)
        for row in standings_rows
    }
    normalized_matches = [_normalize_match_row(match) for match in matches_rows]
    group_context_by_code = build_group_context(normalized_matches)
    knockout_active = knockout_phase_active(normalized_matches)
    knockout_context_by_code = build_knockout_context(
        _group_matches_by_team(normalized_matches),
        standings_by_code,
        knockout_active,
    )

    enriched: list[dict[str, Any]] = []
    for item in leaderboard_inputs:
        row = dict(item)
        team_code = resolve_team_code(str(row.get("team_name") or ""), row.get("team_code"))
        row["team_code"] = team_code
        context = knockout_context_by_code.get(team_code)
        standing = standings_by_code.get(team_code)
        group_context = group_context_by_code.get(team_code)
        row["contributing_points"] = int(row.get("points", 0))
        row["advancement_bonus"] = context.advancement_bonus if (context and knockout_active) else 0
        row["alive"] = int(
            effective_alive(
                fallback=row.get("alive", 1),
                standing=standing,
                group_context=group_context,
                knockout_context=context,
                knockout_active=knockout_active,
            )
        )
        enriched.append(row)
    return enriched


def knockout_phase_active(matches_rows: list[dict[str, Any]]) -> bool:
    return any(is_knockout_stage(match.get("stage")) for match in matches_rows)


def build_knockout_context(
    matches_by_code: dict[str, list[dict[str, Any]]],
    standings_by_code: dict[str, dict[str, Any]],
    knockout_active: bool,
) -> dict[str, KnockoutContext]:
    if not knockout_active:
        return {}

    contexts: dict[str, KnockoutContext] = {}
    for team_code, team_matches in matches_by_code.items():
        knockout_matches = [match for match in team_matches if is_knockout_stage(match.get("stage"))]
        if not knockout_matches:
            continue

        upcoming = [match for match in knockout_matches if not is_completed(match)]
        completed = [match for match in knockout_matches if is_completed(match)]
        if upcoming:
            next_match = min(upcoming, key=lambda match: str(match["match_date"]))
            contexts[team_code] = KnockoutContext(
                stage_label=_stage_label(next_match.get("stage")),
                advancement_bonus=stage_bonus(next_match.get("stage")),
                is_active=True,
            )
            continue

        latest = max(completed, key=lambda match: str(match["match_date"]), default=None)
        if latest is None:
            continue

        winning_code = winner_code(latest)
        if _stage_label(latest.get("stage")) == "Final" and winning_code == team_code:
            contexts[team_code] = KnockoutContext(
                stage_label="Champion",
                advancement_bonus=stage_bonus(latest.get("stage")),
                is_active=False,
            )
        elif winning_code == team_code:
            next_stage = next_stage_label(latest.get("stage"))
            contexts[team_code] = KnockoutContext(
                stage_label=next_stage,
                advancement_bonus=stage_bonus(next_stage),
                is_active="THIRD" not in str(latest.get("stage") or "").upper(),
            )
        elif winning_code:
            contexts[team_code] = KnockoutContext(
                stage_label=f'Eliminated in {_stage_label(latest.get("stage"))}',
                advancement_bonus=stage_bonus(latest.get("stage")),
                latest_elimination_match=latest,
                is_active=False,
            )
        else:
            alive = alive_flag(standings_by_code.get(team_code, {}).get("alive", 1))
            contexts[team_code] = KnockoutContext(
                stage_label=(
                    next_stage_label(latest.get("stage"))
                    if alive
                    else f'Eliminated in {_stage_label(latest.get("stage"))}'
                ),
                advancement_bonus=(
                    stage_bonus(next_stage_label(latest.get("stage")))
                    if alive
                    else stage_bonus(latest.get("stage"))
                ),
                latest_elimination_match=None if alive else latest,
                is_active=alive,
            )
    return contexts


def effective_alive(
    *,
    fallback: Any,
    standing: dict[str, Any] | None,
    group_context: dict[str, Any] | None = None,
    knockout_context: KnockoutContext | None,
    knockout_active: bool,
) -> bool:
    if knockout_active and knockout_context is not None:
        return knockout_context.is_active
    if knockout_active:
        merged_group_context = dict(group_context or {})
        if standing:
            merged_group_context = merged_group_context | standing
        if standing is None and not merged_group_context:
            return False
        qualification = str((standing or {}).get("qualification_status") or "").lower()
        group_position = normalized_group_position(merged_group_context)
        played = safe_int(merged_group_context.get("played")) or 0
        if "eliminated" in qualification:
            return False
        if any(keyword in qualification for keyword in ("qualified", "advance", "playoff")):
            return True
        if group_position is not None and played >= 3 and group_position > 2:
            return False
        if group_position is not None and played >= 3 and group_position <= 2:
            return True
    return alive_flag(fallback)


def is_knockout_stage(stage: Any) -> bool:
    value = str(stage or "").upper()
    return bool(value) and "GROUP" not in value and "FIRST_STAGE" not in value and "FIRSTSTAGE" not in value


def stage_bonus(stage: Any) -> int:
    value = str(stage or "").upper()
    if "FINAL" in value and "SEMI" not in value and "QUARTER" not in value and "THIRD" not in value:
        return 10 + 20 + 30 + 40 + 50
    if "THIRD" in value:
        return 10 + 20 + 30 + 40
    if "SEMI" in value:
        return 10 + 20 + 30 + 40
    if "QUARTER" in value:
        return 10 + 20 + 30
    if "16" in value:
        return 10 + 20
    if "32" in value or "PLAYOFF" in value:
        return 10
    return 0


def next_stage_label(stage: Any) -> str:
    value = str(stage or "").upper()
    if "32" in value or "PLAYOFF" in value:
        return "Round of 16"
    if "16" in value:
        return "Quarter-finals"
    if "QUARTER" in value:
        return "Semi-finals"
    if "SEMI" in value:
        return "Final"
    if "THIRD" in value:
        return "Third place"
    if "FINAL" in value:
        return "Champion"
    return "Knockout stage"


def winner_code(match: dict[str, Any]) -> str | None:
    winner = str(match.get("winner") or "").upper()
    if winner == "HOME_TEAM":
        return str(match.get("home_team_code") or "")
    if winner == "AWAY_TEAM":
        return str(match.get("away_team_code") or "")
    home_score = safe_int(match.get("home_score")) or 0
    away_score = safe_int(match.get("away_score")) or 0
    if home_score > away_score:
        return str(match.get("home_team_code") or "")
    if away_score > home_score:
        return str(match.get("away_team_code") or "")
    return None


def normalized_group_position(standing: dict[str, Any] | None) -> int | None:
    if not standing:
        return None
    position = safe_int(standing.get("group_position"))
    if position is None or position < 1 or position > 4:
        return None
    return position


def alive_flag(value: Any) -> bool:
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"", "0", "false", "no", "n"}:
            return False
        if cleaned in {"1", "true", "yes", "y"}:
            return True
    return bool(value)


def is_completed(match: dict[str, Any]) -> bool:
    return str(match.get("status", "")).upper() in {"FINISHED", "FT", "AET", "PEN"}


def safe_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _normalize_match_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["home_team_code"] = resolve_team_code(str(normalized.get("home_team") or ""), normalized.get("home_team_code"))
    normalized["away_team_code"] = resolve_team_code(str(normalized.get("away_team") or ""), normalized.get("away_team_code"))
    return normalized


def _group_matches_by_team(matches_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for match in matches_rows:
        home_code = str(match.get("home_team_code") or "")
        away_code = str(match.get("away_team_code") or "")
        if home_code:
            grouped.setdefault(home_code, []).append(match)
        if away_code:
            grouped.setdefault(away_code, []).append(match)
    return grouped


def build_group_context(matches_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for match in matches_rows:
        if str(match.get("stage") or "").upper() != "GROUP_STAGE":
            continue
        group_name = str(match.get("group_name") or "")
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
        if not is_completed(match):
            continue

        home_score = safe_int(match.get("home_score"))
        away_score = safe_int(match.get("away_score"))
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
        elif away_score > home_score:
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
            key=lambda row: (
                -row["points"],
                -(row["goals_for"] - row["goals_against"]),
                -row["goals_for"],
                row["team_name"].lower(),
            ),
        )
        for index, row in enumerate(ordered, start=1):
            by_team[row["team_code"]] = {
                "group_name": row["group_name"],
                "group_position": index,
                "played": row["played"],
                "points": row["points"],
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
