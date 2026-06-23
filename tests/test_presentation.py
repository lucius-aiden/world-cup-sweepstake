from datetime import UTC, datetime

from src.models import TeamOdds
from src.presentation import build_dashboard_view, determine_team_status


class StubSettings:
    raw = {
        "app": {"timezone": "Europe/London"},
        "tournament": {"name": "FIFA World Cup 2026"},
    }


def test_dashboard_view_builds_expandable_team_card_data():
    inputs = [
        {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
        {"player": "Alice", "team_slot": 2, "team_name": "Panama", "team_code": "PAN", "points": 1, "alive": 1},
    ]
    standings = [
        {
            "team_code": "BRA",
            "team_name": "Brazil",
            "group_name": "Group A",
            "group_position": 1,
            "played": 3,
            "won": 2,
            "drawn": 1,
            "lost": 0,
            "goals_for": 5,
            "goals_against": 2,
            "goal_difference": 3,
            "points": 7,
            "alive": 1,
            "qualification_status": "Qualified",
        },
        {
            "team_code": "PAN",
            "team_name": "Panama",
            "group_name": "Group A",
            "group_position": 3,
            "played": 2,
            "won": 0,
            "drawn": 1,
            "lost": 1,
            "goals_for": 1,
            "goals_against": 3,
            "goal_difference": -2,
            "points": 1,
            "alive": 1,
            "qualification_status": None,
        },
    ]
    matches = [
        {
            "match_id": "1",
            "home_team": "Brazil",
            "home_team_code": "BRA",
            "away_team": "Japan",
            "away_team_code": "JPN",
            "home_score": 2,
            "away_score": 0,
            "status": "FINISHED",
            "match_date": datetime(2026, 6, 22, 18, 0, tzinfo=UTC).isoformat(),
            "stage": "GROUP_STAGE",
            "winner": "HOME_TEAM",
        },
        {
            "match_id": "2",
            "home_team": "Norway",
            "home_team_code": "NOR",
            "away_team": "Brazil",
            "away_team_code": "BRA",
            "home_score": None,
            "away_score": None,
            "status": "TIMED",
            "match_date": datetime(2026, 6, 25, 18, 0, tzinfo=UTC).isoformat(),
            "stage": "GROUP_STAGE",
            "winner": None,
        },
    ]

    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=inputs,
        standings_rows=standings,
        matches_rows=matches,
        odds_by_team={"BRA": TeamOdds("BRA", "Brazil", 5.5)},
        now=datetime(2026, 6, 23, 7, 0, tzinfo=UTC),
    )

    row = view.leaderboard_rows[0]
    assert row.player == "Alice"
    assert row.team_1.team_name == "Brazil"
    assert row.team_1.status.label == "Qualified"
    assert row.team_1.form == ["W"]
    assert row.team_1.last_match is not None
    assert row.team_1.next_match is not None
    assert row.team_1.win_odds == "5.50"


def test_dashboard_view_hides_out_of_range_group_positions():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Germany", "team_code": "GER", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
        ],
        standings_rows=[
            {
                "team_code": "GER",
                "team_name": "Germany",
                "group_name": None,
                "group_position": 22,
                "played": 2,
                "won": 2,
                "drawn": 0,
                "lost": 0,
                "goals_for": 7,
                "goals_against": 0,
                "goal_difference": 7,
                "points": 6,
                "alive": 1,
                "qualification_status": None,
            },
            {
                "team_code": "FRA",
                "team_name": "France",
                "group_name": None,
                "group_position": 26,
                "played": 2,
                "won": 2,
                "drawn": 0,
                "lost": 0,
                "goals_for": 5,
                "goals_against": 0,
                "goal_difference": 5,
                "points": 6,
                "alive": 1,
                "qualification_status": None,
            },
        ],
        matches_rows=[],
    )

    row = view.leaderboard_rows[0]
    assert row.team_1.group_label == "Group position TBD"
    assert row.team_1.status.label == "Alive"


def test_determine_team_status_uses_deterministic_labels():
    assert determine_team_status({"alive": 0, "group_position": 4, "played": 3}).label == "Eliminated"
    assert determine_team_status({"alive": 1, "group_position": 1, "played": 3}).label == "Qualified"
    assert determine_team_status({"alive": 1, "group_position": 3, "played": 2}).label == "At Risk"
    assert determine_team_status({"alive": 1, "group_position": 2, "played": 1}).label == "Alive"
    assert determine_team_status({"alive": 1, "group_position": 4, "played": 1}).label == "Alive"
    assert determine_team_status({"alive": 1, "group_position": 22, "played": 2}).label == "Alive"
