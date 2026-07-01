from datetime import UTC, datetime

from src.models import LeaderboardRow, Match
from src.teams import render_message


def test_render_message_marks_penalty_shootout_scores_clearly():
    match = Match(
        match_id="9",
        home_team="England",
        away_team="Japan",
        home_team_code="ENG",
        away_team_code="JPN",
        home_score=5,
        away_score=4,
        status="PEN",
        match_date=datetime.now(UTC),
        winner="HOME_TEAM",
        score_duration="PENALTY_SHOOTOUT",
        regular_home_score=1,
        regular_away_score=1,
        extra_home_score=0,
        extra_away_score=0,
        penalty_home_score=4,
        penalty_away_score=3,
    )

    message = render_message(
        match,
        affected_players=[],
        leaderboard=[LeaderboardRow("Alice", "England", 4, "Still in", "Japan", 4, "Knocked out", 8, 1, 1)],
        top_n_summary=1,
    )

    assert "England 1-1 Japan (pens 4-3)" in message
