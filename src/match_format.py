from __future__ import annotations

from typing import Any, Mapping

from .models import Match


def format_match_scoreline(match: Mapping[str, Any] | Match) -> str:
    home_team = str(_field(match, "home_team") or "")
    away_team = str(_field(match, "away_team") or "")
    home_score = _int_field(match, "home_score")
    away_score = _int_field(match, "away_score")

    score_text = f"{home_score}-{away_score}" if home_score is not None and away_score is not None else "vs"
    result = f"{home_team} {score_text} {away_team}".strip()

    if _score_duration(match) == "PENALTY_SHOOTOUT":
        pre_home, pre_away = _pre_shootout_score(match)
        if pre_home is not None and pre_away is not None:
            result = f"{home_team} {pre_home}-{pre_away} {away_team}"
        pens_home = _int_field(match, "penalty_home_score")
        pens_away = _int_field(match, "penalty_away_score")
        if pens_home is not None and pens_away is not None:
            return f"{result} (pens {pens_home}-{pens_away})"
        return f"{result} (pens)"

    if _score_duration(match) == "EXTRA_TIME":
        return f"{result} (AET)"
    return result


def _score_duration(match: Mapping[str, Any] | Match) -> str:
    duration = str(_field(match, "score_duration") or "").upper()
    if duration:
        return duration

    status = str(_field(match, "status") or "").upper()
    if status == "PEN":
        return "PENALTY_SHOOTOUT"
    if status == "AET":
        return "EXTRA_TIME"
    return ""


def _pre_shootout_score(match: Mapping[str, Any] | Match) -> tuple[int | None, int | None]:
    regular_home = _int_field(match, "regular_home_score")
    regular_away = _int_field(match, "regular_away_score")
    extra_home = _int_field(match, "extra_home_score")
    extra_away = _int_field(match, "extra_away_score")

    if regular_home is None or regular_away is None:
        return _int_field(match, "home_score"), _int_field(match, "away_score")

    return regular_home + (extra_home or 0), regular_away + (extra_away or 0)


def _field(match: Mapping[str, Any] | Match, name: str) -> Any:
    if isinstance(match, Mapping):
        return match.get(name)
    return getattr(match, name, None)


def _int_field(match: Mapping[str, Any] | Match, name: str) -> int | None:
    value = _field(match, name)
    if value is None:
        return None
    return int(value)
