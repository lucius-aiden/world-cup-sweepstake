from datetime import UTC, datetime

from src.models import LeaderboardRow, Match
from src.scheduler import _affected_players


def test_affected_players_handles_country_aliases():
    match = Match(
        match_id="1",
        home_team="United States",
        away_team="Brazil",
        home_team_code="USA",
        away_team_code="BRA",
        home_score=1,
        away_score=2,
        status="FINISHED",
        match_date=datetime.now(UTC),
    )
    leaderboard = [
        LeaderboardRow("Sarah", "Brazil", 6, "Alive", "USA", 4, "Alive", 10, 2, 1),
        LeaderboardRow("Tom", "England", 5, "Alive", "Japan", 5, "Alive", 10, 2, 2),
    ]

    affected = _affected_players(
        match,
        previous_ranks={"Sarah": 2, "Tom": 1},
        previous_points={"Sarah": 8, "Tom": 10},
        leaderboard=leaderboard,
    )

    assert [record.player for record in affected] == ["Sarah"]
    assert affected[0].previous_rank == 2
    assert affected[0].new_rank == 1
    assert affected[0].impacted_teams == ("Brazil", "USA")
