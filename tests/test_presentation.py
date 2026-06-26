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
            "group_name": "GROUP_A",
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
            "group_name": "GROUP_A",
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
    assert row.team_1.group_label == "Group A · 1st"
    assert row.team_1.status.label == "Qualified"
    assert row.team_1.form == ["W"]
    assert row.team_1.last_match is not None
    assert row.team_1.next_match is not None
    assert row.team_1.win_odds == "1 in 6 chance (18.2%)"
    assert "10-point bonus for each knockout match they win" in view.leaderboard_blurb
    assert view.home_href == "/"


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


def test_qualified_group_team_keeps_group_label_until_knockout_match_exists():
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
                "group_name": "Group C",
                "group_position": 2,
                "played": 3,
                "won": 2,
                "drawn": 0,
                "lost": 1,
                "goals_for": 5,
                "goals_against": 3,
                "goal_difference": 2,
                "points": 6,
                "alive": 1,
                "qualification_status": "Qualified",
            },
            {
                "team_code": "FRA",
                "team_name": "France",
                "group_name": "Group B",
                "group_position": 1,
                "played": 3,
                "won": 3,
                "drawn": 0,
                "lost": 0,
                "goals_for": 7,
                "goals_against": 1,
                "goal_difference": 6,
                "points": 9,
                "alive": 1,
                "qualification_status": "Qualified",
            },
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Brazil",
                "home_team_code": "BRA",
                "away_team": "Japan",
                "away_team_code": "JPN",
                "home_score": 1,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 7, 1, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": "HOME_TEAM",
            },
        ],
    )

    row = view.leaderboard_rows[0]
    assert row.team_1.group_label == "Group C · 2nd"
    assert row.team_1.status.label == "Qualified"


def test_dashboard_view_orders_homepage_sections_and_dev_links():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Germany", "team_code": "GER", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
        ],
        standings_rows=[],
        matches_rows=[],
        site_base_path="/dev",
    )

    assert [section.title for section in view.insight_sections] == [
        "Top Matches",
        "Today's Key Fixtures",
        "Best Performing Teams",
        "Teams In Trouble",
        "Latest Results",
    ]
    assert view.home_href == "/dev/"


def test_form_runs_left_to_right_in_match_order():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
        ],
        standings_rows=[],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Brazil",
                "home_team_code": "BRA",
                "away_team": "Japan",
                "away_team_code": "JPN",
                "home_score": 2,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 20, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_A",
            },
            {
                "match_id": "2",
                "home_team": "Norway",
                "home_team_code": "NOR",
                "away_team": "Brazil",
                "away_team_code": "BRA",
                "home_score": 1,
                "away_score": 1,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 22, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_A",
            },
        ],
    )

    assert view.leaderboard_rows[0].team_1.form == ["W", "D"]


def test_determine_team_status_uses_deterministic_labels():
    assert determine_team_status({"alive": 0, "group_position": 4, "played": 3}).label == "Eliminated"
    assert determine_team_status({"alive": 1, "group_position": 1, "played": 3}).label == "Qualified"
    assert determine_team_status({"alive": 1, "knockout_phase": True}).label == "Qualified"
    assert determine_team_status({"alive": 1, "group_position": 3, "played": 2}).label == "At Risk"
    assert determine_team_status({"alive": 1, "group_position": 2, "played": 1}).label == "Alive"
    assert determine_team_status({"alive": 1, "group_position": 4, "played": 1}).label == "Alive"
    assert determine_team_status({"alive": 1, "group_position": 22, "played": 2}).label == "Alive"


def test_insights_use_recent_top_matches_and_worst_trouble_ordering():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
        ],
        standings_rows=[
            {
                "team_code": "PAN",
                "team_name": "Panama",
                "group_name": "Group A",
                "group_position": 4,
                "played": 3,
                "won": 0,
                "drawn": 0,
                "lost": 3,
                "goals_for": 1,
                "goals_against": 6,
                "goal_difference": -5,
                "points": 0,
                "alive": 0,
                "qualification_status": "Eliminated",
            },
            {
                "team_code": "JPN",
                "team_name": "Japan",
                "group_name": "Group A",
                "group_position": 3,
                "played": 3,
                "won": 1,
                "drawn": 0,
                "lost": 2,
                "goals_for": 2,
                "goals_against": 4,
                "goal_difference": -2,
                "points": 3,
                "alive": 1,
                "qualification_status": None,
            },
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Brazil",
                "home_team_code": "BRA",
                "away_team": "Japan",
                "away_team_code": "JPN",
                "home_score": 4,
                "away_score": 2,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 22, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_A",
            },
            {
                "match_id": "2",
                "home_team": "France",
                "home_team_code": "FRA",
                "away_team": "Panama",
                "away_team_code": "PAN",
                "home_score": 3,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 23, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_A",
            },
            {
                "match_id": "3",
                "home_team": "Germany",
                "home_team_code": "GER",
                "away_team": "Mexico",
                "away_team_code": "MEX",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 6, 24, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_B",
            },
            {
                "match_id": "4",
                "home_team": "Norway",
                "home_team_code": "NOR",
                "away_team": "Spain",
                "away_team_code": "ESP",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 6, 24, 20, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_B",
            },
        ],
        now=datetime(2026, 6, 24, 7, 0, tzinfo=UTC),
    )

    section_map = {section.title: section for section in view.insight_sections}
    assert [item.title for item in section_map["Top Matches"].items] == ["🇧🇷 Brazil", "🇫🇷 France"]
    assert [item.title for item in section_map["Teams In Trouble"].items] == ["🇵🇦 Panama [Unassigned]", "🇯🇵 Japan [Unassigned]"]


def test_fixture_day_includes_overnight_kickoffs_until_five_am_bst():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
        ],
        standings_rows=[],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Japan",
                "home_team_code": "JPN",
                "away_team": "Mexico",
                "away_team_code": "MEX",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 6, 25, 1, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_A",
            },
            {
                "match_id": "2",
                "home_team": "Norway",
                "home_team_code": "NOR",
                "away_team": "Spain",
                "away_team_code": "ESP",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 6, 25, 5, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_A",
            },
        ],
        now=datetime(2026, 6, 24, 21, 0, tzinfo=UTC),
    )

    section_map = {section.title: section for section in view.insight_sections}
    assert [item.title for item in section_map["Today's Key Fixtures"].items] == ["🇯🇵 Japan vs 🇲🇽 Mexico"]


def test_knockout_rankings_keep_group_points_and_add_heavy_stage_bonus():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 7, "alive": 0},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
            {"player": "Bob", "team_slot": 1, "team_name": "Germany", "team_code": "GER", "points": 7, "alive": 1},
            {"player": "Bob", "team_slot": 2, "team_name": "Spain", "team_code": "ESP", "points": 5, "alive": 1},
            {"player": "Cara", "team_slot": 1, "team_name": "Japan", "team_code": "JPN", "points": 6, "alive": 0},
            {"player": "Cara", "team_slot": 2, "team_name": "Mexico", "team_code": "MEX", "points": 6, "alive": 0},
        ],
        standings_rows=[
            {"team_code": "BRA", "team_name": "Brazil", "group_name": "Group A", "group_position": 1, "played": 3, "won": 2, "drawn": 1, "lost": 0, "goals_for": 5, "goals_against": 2, "goal_difference": 3, "points": 7, "alive": 0, "qualification_status": "Eliminated"},
            {"team_code": "FRA", "team_name": "France", "group_name": "Group B", "group_position": 1, "played": 3, "won": 2, "drawn": 0, "lost": 1, "goals_for": 6, "goals_against": 3, "goal_difference": 3, "points": 6, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "GER", "team_name": "Germany", "group_name": "Group C", "group_position": 1, "played": 3, "won": 2, "drawn": 1, "lost": 0, "goals_for": 7, "goals_against": 2, "goal_difference": 5, "points": 7, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "ESP", "team_name": "Spain", "group_name": "Group D", "group_position": 2, "played": 3, "won": 2, "drawn": 0, "lost": 1, "goals_for": 5, "goals_against": 4, "goal_difference": 1, "points": 5, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "JPN", "team_name": "Japan", "group_name": "Group E", "group_position": 3, "played": 3, "won": 1, "drawn": 0, "lost": 2, "goals_for": 3, "goals_against": 4, "goal_difference": -1, "points": 6, "alive": 0, "qualification_status": "Eliminated"},
            {"team_code": "MEX", "team_name": "Mexico", "group_name": "Group F", "group_position": 3, "played": 3, "won": 1, "drawn": 0, "lost": 2, "goals_for": 2, "goals_against": 5, "goal_difference": -3, "points": 6, "alive": 0, "qualification_status": "Eliminated"},
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Brazil",
                "home_team_code": "BRA",
                "away_team": "Japan",
                "away_team_code": "JPN",
                "home_score": 1,
                "away_score": 2,
                "status": "FINISHED",
                "match_date": datetime(2026, 7, 1, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": "AWAY_TEAM",
            },
            {
                "match_id": "2",
                "home_team": "France",
                "home_team_code": "FRA",
                "away_team": "Portugal",
                "away_team_code": "POR",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 6, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "QUARTER_FINALS",
            },
            {
                "match_id": "3",
                "home_team": "Germany",
                "home_team_code": "GER",
                "away_team": "Italy",
                "away_team_code": "ITA",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 3, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
            },
            {
                "match_id": "4",
                "home_team": "Spain",
                "home_team_code": "ESP",
                "away_team": "Morocco",
                "away_team_code": "MAR",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 3, 21, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
            },
        ],
        now=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
    )

    assert [row.player for row in view.leaderboard_rows] == ["Alice", "Bob", "Cara"]
    assert view.leaderboard_rows[0].total_points == 43
    assert view.leaderboard_rows[1].total_points == 32
    assert view.leaderboard_rows[2].total_points == 22
    assert view.leaderboard_rows[0].team_1.group_label == "Eliminated in Round of 16"
    assert view.leaderboard_rows[0].team_2.group_label == "Quarter-finals"

    section_map = {section.title: section for section in view.insight_sections}
    assert section_map["Latest Knockouts"].items[0].title == "🇧🇷 Brazil [Alice]"
    assert section_map["Best Performing Teams"].items[0].title == "🇫🇷 France [Alice]"


def test_knockout_phase_keeps_teams_in_trouble_until_first_elimination():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Germany", "team_code": "GER", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 9, "alive": 1},
        ],
        standings_rows=[
            {"team_code": "GER", "team_name": "Germany", "group_name": "Group C", "group_position": 2, "played": 3, "won": 2, "drawn": 0, "lost": 1, "goals_for": 5, "goals_against": 3, "goal_difference": 2, "points": 6, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "FRA", "team_name": "France", "group_name": "Group B", "group_position": 1, "played": 3, "won": 3, "drawn": 0, "lost": 0, "goals_for": 7, "goals_against": 1, "goal_difference": 6, "points": 9, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "PAN", "team_name": "Panama", "group_name": "Group A", "group_position": 4, "played": 3, "won": 0, "drawn": 0, "lost": 3, "goals_for": 1, "goals_against": 6, "goal_difference": -5, "points": 0, "alive": 0, "qualification_status": "Eliminated"},
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Germany",
                "home_team_code": "GER",
                "away_team": "Portugal",
                "away_team_code": "POR",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 6, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "QUARTER_FINALS",
            },
        ],
    )

    section_map = {section.title: section for section in view.insight_sections}
    assert "Teams In Trouble" in section_map
    assert [item.title for item in section_map["Teams In Trouble"].items] == ["🇵🇦 Panama [Unassigned]"]


def test_team_one_stage_further_always_beats_group_stage_gap():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 9, "alive": 0},
            {"player": "Alice", "team_slot": 2, "team_name": "Japan", "team_code": "JPN", "points": 0, "alive": 0},
            {"player": "Bob", "team_slot": 1, "team_name": "Germany", "team_code": "GER", "points": 0, "alive": 1},
            {"player": "Bob", "team_slot": 2, "team_name": "Spain", "team_code": "ESP", "points": 0, "alive": 0},
        ],
        standings_rows=[
            {"team_code": "BRA", "team_name": "Brazil", "group_name": "Group A", "group_position": 1, "played": 3, "won": 3, "drawn": 0, "lost": 0, "goals_for": 6, "goals_against": 1, "goal_difference": 5, "points": 9, "alive": 0, "qualification_status": "Eliminated"},
            {"team_code": "JPN", "team_name": "Japan", "group_name": "Group B", "group_position": 4, "played": 3, "won": 0, "drawn": 0, "lost": 3, "goals_for": 1, "goals_against": 7, "goal_difference": -6, "points": 0, "alive": 0, "qualification_status": "Eliminated"},
            {"team_code": "GER", "team_name": "Germany", "group_name": "Group C", "group_position": 2, "played": 3, "won": 0, "drawn": 0, "lost": 3, "goals_for": 1, "goals_against": 7, "goal_difference": -6, "points": 0, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "ESP", "team_name": "Spain", "group_name": "Group D", "group_position": 4, "played": 3, "won": 0, "drawn": 0, "lost": 3, "goals_for": 1, "goals_against": 7, "goal_difference": -6, "points": 0, "alive": 0, "qualification_status": "Eliminated"},
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Brazil",
                "home_team_code": "BRA",
                "away_team": "Mexico",
                "away_team_code": "MEX",
                "home_score": 1,
                "away_score": 2,
                "status": "FINISHED",
                "match_date": datetime(2026, 7, 1, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": "AWAY_TEAM",
            },
            {
                "match_id": "2",
                "home_team": "Germany",
                "home_team_code": "GER",
                "away_team": "Portugal",
                "away_team_code": "POR",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 6, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "QUARTER_FINALS",
            },
        ],
        now=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
    )

    assert [row.player for row in view.leaderboard_rows] == ["Bob", "Alice"]
    assert view.leaderboard_rows[0].total_points == 20
    assert view.leaderboard_rows[1].total_points == 19
