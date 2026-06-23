from datetime import UTC, datetime

from src.models import Match, TeamStanding
from src.standings import build_effective_standings


def test_group_points_are_recomputed_from_completed_matches():
    matches = [
        Match("1", "Argentina", "Austria", 2, 0, "FINISHED", datetime(2026, 6, 20, tzinfo=UTC), stage="GROUP_STAGE"),
        Match("2", "Jordan", "Algeria", 1, 1, "FINISHED", datetime(2026, 6, 21, tzinfo=UTC), stage="GROUP_STAGE"),
        Match("3", "Argentina", "Jordan", 0, 0, "FINISHED", datetime(2026, 6, 22, tzinfo=UTC), stage="GROUP_STAGE"),
    ]
    provider = [
        TeamStanding("ARG", "Argentina", 2, 0, 0, 0, 0, 0, 0, 0, True),
        TeamStanding("AUT", "Austria", 1, 0, 0, 0, 0, 0, 0, 99, True),
        TeamStanding("JOR", "Jordan", 2, 0, 0, 0, 0, 0, 0, 99, True),
        TeamStanding("ALG", "Algeria", 1, 0, 0, 0, 0, 0, 0, 99, False),
    ]

    standings = {row.team_code: row for row in build_effective_standings(matches, provider)}

    assert standings["ARG"].points == 4
    assert standings["AUT"].points == 0
    assert standings["JOR"].points == 2
    assert standings["ALG"].points == 1
    assert standings["ALG"].alive is False
