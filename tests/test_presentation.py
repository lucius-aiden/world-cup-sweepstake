from datetime import UTC, datetime

from src.models import TeamOdds, TopScorer
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
        top_scorers=[
            TopScorer("Vinicius Junior", "Brazil", "BRA", 4, 3, 0),
            TopScorer("Rico Lewis", "England", "ENG", 1, 0, 0),
        ],
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
    assert row.team_1.top_scorer == "Vinicius Junior (4 goals)"
    assert row.team_2.top_scorer is None
    assert row.team_1.win_odds == "1 in 6 chance (18.2%)"
    assert "10 for the round of 32" in view.leaderboard_blurb
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


def test_dashboard_view_formats_penalty_shootouts_without_looking_like_goal_fests():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "England", "team_code": "ENG", "points": 4, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "Japan", "team_code": "JPN", "points": 4, "alive": 0},
        ],
        standings_rows=[
            {
                "team_code": "ENG",
                "team_name": "England",
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
                "team_code": "JPN",
                "team_name": "Japan",
                "group_name": "Group B",
                "group_position": 2,
                "played": 3,
                "won": 1,
                "drawn": 1,
                "lost": 1,
                "goals_for": 3,
                "goals_against": 3,
                "goal_difference": 0,
                "points": 4,
                "alive": 0,
                "qualification_status": "Eliminated",
            },
        ],
        matches_rows=[
            {
                "match_id": "77",
                "home_team": "England",
                "home_team_code": "ENG",
                "away_team": "Japan",
                "away_team_code": "JPN",
                "home_score": 5,
                "away_score": 4,
                "regular_home_score": 1,
                "regular_away_score": 1,
                "extra_home_score": 0,
                "extra_away_score": 0,
                "penalty_home_score": 4,
                "penalty_away_score": 3,
                "score_duration": "PENALTY_SHOOTOUT",
                "status": "PEN",
                "match_date": datetime(2026, 7, 4, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "QUARTER_FINALS",
                "winner": "HOME_TEAM",
            },
        ],
        now=datetime(2026, 7, 5, 7, 0, tzinfo=UTC),
    )

    assert view.latest_result == "England 1-1 Japan (pens 4-3)"
    assert view.leaderboard_rows[0].team_1.last_match is not None
    assert view.leaderboard_rows[0].team_1.last_match.title == "England 1-1 Japan (pens 4-3)"
    section_map = {section.title: section for section in view.insight_sections}
    assert section_map["Latest Knockouts"].items[0].detail.startswith("Quarter-finals · England 1-1 Japan (pens 4-3)")


def test_eliminated_team_card_hides_next_match():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 7, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
        ],
        standings_rows=[
            {"team_code": "BRA", "team_name": "Brazil", "group_name": "Group A", "group_position": 1, "played": 3, "won": 2, "drawn": 1, "lost": 0, "goals_for": 5, "goals_against": 2, "goal_difference": 3, "points": 7, "alive": 0, "qualification_status": "Eliminated"},
            {"team_code": "FRA", "team_name": "France", "group_name": "Group B", "group_position": 1, "played": 3, "won": 2, "drawn": 0, "lost": 1, "goals_for": 6, "goals_against": 3, "goal_difference": 3, "points": 6, "alive": 1, "qualification_status": "Qualified"},
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
                "away_team": "Spain",
                "away_team_code": "ESP",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 6, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "QUARTER_FINALS",
            },
        ],
        now=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
    )

    row = view.leaderboard_rows[0]
    assert row.team_1.status.label == "Eliminated"
    assert row.team_1.next_match is None
    assert row.team_2.next_match is not None


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
        top_scorers=[TopScorer("Kylian Mbappe", "France", "FRA", 6, 2, 1)],
        site_base_path="/dev",
    )

    assert [section.title for section in view.insight_sections] == [
        "Top Matches",
        "Today's Key Fixtures",
        "Top Scorers",
        "Best Performing Teams",
        "Teams In Trouble",
        "Latest Results",
    ]
    assert view.home_href == "/dev/"


def test_top_scorers_section_uses_competition_scorer_feed():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
        ],
        standings_rows=[],
        matches_rows=[],
        top_scorers=[
            TopScorer("Kylian Mbappe", "France", "FRA", 6, 2, 1),
            TopScorer("Vinicius Junior", "Brazil", "BRA", 4, 3, 0),
        ],
    )

    section_map = {section.title: section for section in view.insight_sections}
    assert [item.title for item in section_map["Top Scorers"].items] == [
        "🇫🇷 Kylian Mbappe",
        "🇧🇷 Vinicius Junior",
    ]
    assert section_map["Top Scorers"].items[0].detail == "France [Alice] · 6 goals · 2 assists · 1 pens"


def test_team_card_uses_highest_goal_scorer_for_each_team():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
        ],
        standings_rows=[],
        matches_rows=[],
        top_scorers=[
            TopScorer("Kylian Mbappe", "France", "FRA", 6, 2, 1),
            TopScorer("Ousmane Dembele", "France", "FRA", 4, 4, 0),
            TopScorer("Vinicius Junior", "Brazil", "BRA", 4, 3, 0),
        ],
    )

    row = view.leaderboard_rows[0]
    assert row.team_1.top_scorer == "Kylian Mbappe (6 goals)"
    assert row.team_2.top_scorer == "Vinicius Junior (4 goals)"


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
    assert view.leaderboard_rows[0].total_points == 103
    assert view.leaderboard_rows[1].total_points == 72
    assert view.leaderboard_rows[2].total_points == 72
    assert view.leaderboard_rows[0].team_1.group_label == "Eliminated in Round of 16"
    assert view.leaderboard_rows[0].team_2.group_label == "Quarter-finals"
    assert view.leaderboard_rows[2].team_1.group_label == "Quarter-finals"

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


def test_knockout_loss_overrides_stale_qualified_status_and_best_performing_lists():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "South Africa", "team_code": "RSA", "points": 4, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "Canada", "team_code": "CAN", "points": 7, "alive": 1},
        ],
        standings_rows=[
            {"team_code": "RSA", "team_name": "South Africa", "group_name": "Group B", "group_position": 2, "played": 3, "won": 1, "drawn": 1, "lost": 1, "goals_for": 4, "goals_against": 4, "goal_difference": 0, "points": 4, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "CAN", "team_name": "Canada", "group_name": "Group A", "group_position": 1, "played": 3, "won": 2, "drawn": 1, "lost": 0, "goals_for": 6, "goals_against": 2, "goal_difference": 4, "points": 7, "alive": 1, "qualification_status": "Qualified"},
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Canada",
                "home_team_code": "CAN",
                "away_team": "South Africa",
                "away_team_code": "RSA",
                "home_score": 2,
                "away_score": 1,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 29, 8, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": "HOME_TEAM",
            },
        ],
    )

    row = view.leaderboard_rows[0]
    assert row.team_1.status.label == "Eliminated"
    assert row.team_1.group_label == "Eliminated in Round of 16"
    assert row.teams_alive == 1

    section_map = {section.title: section for section in view.insight_sections}
    best_titles = [item.title for item in section_map["Best Performing Teams"].items]
    assert "🇿🇦 South Africa [Alice]" not in best_titles
    assert best_titles == ["🇨🇦 Canada [Alice]"]


def test_dashboard_view_normalizes_provider_team_codes_for_participant_cards():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Celine", "team_slot": 1, "team_name": "Saudi Arabia", "team_code": "KSA", "points": 1, "alive": 1},
            {"player": "Celine", "team_slot": 2, "team_name": "Haiti", "team_code": "HTI", "points": 1, "alive": 1},
        ],
        standings_rows=[
            {"team_code": "HAI", "team_name": "Haiti", "group_name": "Group F", "group_position": 3, "played": 3, "won": 0, "drawn": 1, "lost": 2, "goals_for": 2, "goals_against": 6, "goal_difference": -4, "points": 1, "alive": 0, "qualification_status": "Eliminated"},
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Morocco",
                "home_team_code": "MAR",
                "away_team": "Haiti",
                "away_team_code": "HAI",
                "home_score": 4,
                "away_score": 2,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 24, 22, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "group_name": "GROUP_F",
                "winner": "HOME_TEAM",
            },
        ],
    )

    row = view.leaderboard_rows[0]
    assert row.team_2.team_name == "Haiti"
    assert row.team_2.status.label == "Eliminated"
    assert row.team_2.group_label.startswith("Group F · ")
    assert row.team_2.form == ["L"]
    assert row.team_2.last_match is not None
    assert row.team_2.last_match.title == "Morocco 4-2 Haiti"


def test_dashboard_view_normalizes_variant_knockout_team_names_without_provider_codes():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Abhilasha", "team_slot": 1, "team_name": "Uzbekistan", "team_code": "UZB", "points": 3, "alive": 1},
            {"player": "Abhilasha", "team_slot": 2, "team_name": "Turkey", "team_code": "TUR", "points": 3, "alive": 1},
        ],
        standings_rows=[
            {"team_code": "UZB", "team_name": "Uzbekistan", "group_name": "Group H", "group_position": 2, "played": 3, "won": 1, "drawn": 0, "lost": 2, "goals_for": 2, "goals_against": 4, "goal_difference": -2, "points": 3, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "TUR", "team_name": "Turkey", "group_name": "Group G", "group_position": 2, "played": 3, "won": 1, "drawn": 0, "lost": 2, "goals_for": 3, "goals_against": 5, "goal_difference": -2, "points": 3, "alive": 1, "qualification_status": "Qualified"},
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Uzbekistan",
                "home_team_code": "",
                "away_team": "Türkiye",
                "away_team_code": "",
                "home_score": 1,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 29, 12, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "HOME_TEAM",
            },
        ],
    )

    row = view.leaderboard_rows[0]
    assert row.team_2.status.label == "Eliminated"
    assert row.team_2.group_label == "Eliminated in Round of 32"
    assert row.team_2.group_points == 3
    assert row.teams_alive == 1


def test_knockout_active_group_stage_non_qualifiers_show_eliminated_without_knockout_match():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Angela", "team_slot": 1, "team_name": "New Zealand", "team_code": "NZL", "points": 1, "alive": 1},
            {"player": "Angela", "team_slot": 2, "team_name": "South Korea", "team_code": "KOR", "points": 3, "alive": 1},
        ],
        standings_rows=[
            {"team_code": "NZL", "team_name": "New Zealand", "group_name": "Group G", "group_position": 4, "played": 3, "won": 0, "drawn": 1, "lost": 2, "goals_for": 1, "goals_against": 5, "goal_difference": -4, "points": 1, "alive": 1, "qualification_status": None},
            {"team_code": "KOR", "team_name": "South Korea", "group_name": "Group A", "group_position": 3, "played": 3, "won": 1, "drawn": 0, "lost": 2, "goals_for": 2, "goals_against": 3, "goal_difference": -1, "points": 3, "alive": 1, "qualification_status": None},
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Canada",
                "home_team_code": "CAN",
                "away_team": "South Africa",
                "away_team_code": "RSA",
                "home_score": 1,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 29, 12, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "HOME_TEAM",
            },
        ],
    )

    row = view.leaderboard_rows[0]
    assert row.team_1.status.label == "Eliminated"
    assert row.team_2.status.label == "Eliminated"
    assert row.teams_alive == 0
    assert row.team_2.group_label == "Group A · 3rd"

    section_map = {section.title: section for section in view.insight_sections}
    assert section_map["Latest Knockouts"].items[0].title == "🇰🇷 South Korea [Angela]"
    assert section_map["Latest Knockouts"].items[1].title == "🇳🇿 New Zealand [Angela]"


def test_draw_view_builds_rounds_and_marks_winners_and_eliminations():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Bob", "team_slot": 1, "team_name": "Belgium", "team_code": "BEL", "points": 2, "alive": 1},
            {"player": "Bob", "team_slot": 2, "team_name": "Iraq", "team_code": "IRQ", "points": 1, "alive": 1},
            {"player": "Alice", "team_slot": 1, "team_name": "Canada", "team_code": "CAN", "points": 7, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "South Africa", "team_code": "RSA", "points": 4, "alive": 1},
        ],
        standings_rows=[
            {"team_code": "BEL", "team_name": "Belgium", "group_name": "Group X", "group_position": 3, "played": 3, "won": 0, "drawn": 1, "lost": 2, "goals_for": 1, "goals_against": 3, "goal_difference": -2, "points": 1, "alive": 1, "qualification_status": None},
            {"team_code": "IRQ", "team_name": "Iraq", "group_name": "Group X", "group_position": 4, "played": 3, "won": 0, "drawn": 1, "lost": 2, "goals_for": 1, "goals_against": 4, "goal_difference": -3, "points": 1, "alive": 1, "qualification_status": None},
            {"team_code": "CAN", "team_name": "Canada", "group_name": "Group X", "group_position": 1, "played": 3, "won": 3, "drawn": 0, "lost": 0, "goals_for": 6, "goals_against": 1, "goal_difference": 5, "points": 9, "alive": 1, "qualification_status": "Qualified"},
            {"team_code": "RSA", "team_name": "South Africa", "group_name": "Group X", "group_position": 2, "played": 3, "won": 1, "drawn": 1, "lost": 1, "goals_for": 4, "goals_against": 4, "goal_difference": 0, "points": 4, "alive": 1, "qualification_status": "Qualified"},
        ],
        matches_rows=[
            {
                "match_id": "1",
                "home_team": "Canada",
                "home_team_code": "CAN",
                "away_team": "South Africa",
                "away_team_code": "RSA",
                "home_score": 1,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 29, 12, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "HOME_TEAM",
            },
            {
                "match_id": "2",
                "home_team": "Belgium",
                "home_team_code": "BEL",
                "away_team": "Iraq",
                "away_team_code": "IRQ",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 1, 17, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": None,
            },
        ],
    )

    assert [round_view.title for round_view in view.draw_rounds] == [
        "Round of 32",
        "Round of 16",
        "Quarter-finals",
        "Semi-finals",
        "Final",
    ]
    first_match = view.draw_rounds[0].matches[0]
    assert first_match.home_team.won is True
    assert first_match.away_team.eliminated is True
    assert first_match.home_team.owner_label == "Alice"
    second_match = view.draw_rounds[1].matches[0]
    assert second_match.home_team.team_name == "Belgium"
    assert second_match.away_team.team_name == "Iraq"
    assert view.draw_grid_rows == 1
    assert view.draw_rounds[2].matches[0].placeholder is True
    assert view.draw_rounds[2].matches[0].home_team.team_name == "TBD"
    assert view.draw_rounds[2].matches[0].home_team.source_label == "Winner R16 1"


def test_draw_view_orders_knockout_slots_by_predecessor_matches_not_kickoff_time():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[],
        standings_rows=[],
        matches_rows=[
            {
                "match_id": "r32-1",
                "home_team": "Brazil",
                "home_team_code": "BRA",
                "away_team": "Japan",
                "away_team_code": "JPN",
                "home_score": 2,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 29, 12, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "HOME_TEAM",
            },
            {
                "match_id": "r32-2",
                "home_team": "Spain",
                "home_team_code": "ESP",
                "away_team": "Mexico",
                "away_team_code": "MEX",
                "home_score": 1,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 29, 16, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "HOME_TEAM",
            },
            {
                "match_id": "r32-3",
                "home_team": "Germany",
                "home_team_code": "GER",
                "away_team": "Norway",
                "away_team_code": "NOR",
                "home_score": 3,
                "away_score": 1,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 30, 12, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "HOME_TEAM",
            },
            {
                "match_id": "r32-4",
                "home_team": "France",
                "home_team_code": "FRA",
                "away_team": "USA",
                "away_team_code": "USA",
                "home_score": 1,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 30, 16, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "HOME_TEAM",
            },
            {
                "match_id": "r16-late",
                "home_team": "Germany",
                "home_team_code": "GER",
                "away_team": "France",
                "away_team_code": "FRA",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 3, 20, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": None,
            },
            {
                "match_id": "r16-early",
                "home_team": "Brazil",
                "home_team_code": "BRA",
                "away_team": "Spain",
                "away_team_code": "ESP",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 3, 16, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": None,
            },
        ],
    )

    round_of_16 = view.draw_rounds[1].matches
    assert round_of_16[0].home_team.team_name == "Brazil"
    assert round_of_16[0].away_team.team_name == "Spain"
    assert round_of_16[1].home_team.team_name == "Germany"
    assert round_of_16[1].away_team.team_name == "France"


def test_draw_view_reorders_previous_round_to_match_next_round_bracket_path():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[],
        standings_rows=[],
        matches_rows=[
            {
                "match_id": "r32-1",
                "home_team": "Germany",
                "home_team_code": "GER",
                "away_team": "Paraguay",
                "away_team_code": "PAR",
                "home_score": 0,
                "away_score": 1,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 29, 12, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "AWAY_TEAM",
            },
            {
                "match_id": "r32-2",
                "home_team": "Netherlands",
                "home_team_code": "NED",
                "away_team": "Morocco",
                "away_team_code": "MAR",
                "home_score": 0,
                "away_score": 1,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 29, 16, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "AWAY_TEAM",
            },
            {
                "match_id": "r32-3",
                "home_team": "Ivory Coast",
                "home_team_code": "CIV",
                "away_team": "Norway",
                "away_team_code": "NOR",
                "home_score": 0,
                "away_score": 1,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 30, 12, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "AWAY_TEAM",
            },
            {
                "match_id": "r32-4",
                "home_team": "France",
                "home_team_code": "FRA",
                "away_team": "Sweden",
                "away_team_code": "SWE",
                "home_score": 1,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, 30, 16, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_32",
                "winner": "HOME_TEAM",
            },
            {
                "match_id": "r16-1",
                "home_team": "Paraguay",
                "home_team_code": "PAR",
                "away_team": "France",
                "away_team_code": "FRA",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 4, 20, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": None,
            },
            {
                "match_id": "r16-2",
                "home_team": "Morocco",
                "home_team_code": "MAR",
                "away_team": "Norway",
                "away_team_code": "NOR",
                "home_score": None,
                "away_score": None,
                "status": "TIMED",
                "match_date": datetime(2026, 7, 5, 20, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": None,
            },
        ],
    )

    round_of_32 = view.draw_rounds[0].matches
    assert round_of_32[0].away_team.team_name == "Paraguay"
    assert round_of_32[1].home_team.team_name == "France"
    assert round_of_32[2].away_team.team_name == "Morocco"
    assert round_of_32[3].away_team.team_name == "Norway"

    round_of_16 = view.draw_rounds[1].matches
    assert round_of_16[0].home_team.team_name == "Paraguay"
    assert round_of_16[0].away_team.team_name == "France"
    assert round_of_16[1].home_team.team_name == "Morocco"
    assert round_of_16[1].away_team.team_name == "Norway"


def test_latest_results_expand_to_balanced_two_row_snapshot_when_knockouts_exist():
    matches_rows = []
    for match_number in range(1, 11):
        matches_rows.append(
            {
                "match_id": f"group-{match_number}",
                "home_team": f"Home {match_number}",
                "home_team_code": f"H{match_number:02d}",
                "away_team": f"Away {match_number}",
                "away_team_code": f"A{match_number:02d}",
                "home_score": 2,
                "away_score": 1,
                "status": "FINISHED",
                "match_date": datetime(2026, 6, match_number, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "GROUP_STAGE",
                "winner": "HOME_TEAM",
            }
        )
    for match_number in range(1, 6):
        matches_rows.append(
            {
                "match_id": f"ko-{match_number}",
                "home_team": f"Knockout Home {match_number}",
                "home_team_code": f"K{match_number:02d}",
                "away_team": f"Knockout Away {match_number}",
                "away_team_code": f"L{match_number:02d}",
                "home_score": 1,
                "away_score": 0,
                "status": "FINISHED",
                "match_date": datetime(2026, 7, match_number, 18, 0, tzinfo=UTC).isoformat(),
                "stage": "LAST_16",
                "winner": "HOME_TEAM",
            }
        )

    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Knockout Away 1", "team_code": "L01", "points": 0, "alive": 0},
            {"player": "Alice", "team_slot": 2, "team_name": "Knockout Home 1", "team_code": "K01", "points": 0, "alive": 1},
            {"player": "Bob", "team_slot": 1, "team_name": "Knockout Away 2", "team_code": "L02", "points": 0, "alive": 0},
            {"player": "Bob", "team_slot": 2, "team_name": "Knockout Home 2", "team_code": "K02", "points": 0, "alive": 1},
            {"player": "Cara", "team_slot": 1, "team_name": "Knockout Away 3", "team_code": "L03", "points": 0, "alive": 0},
            {"player": "Cara", "team_slot": 2, "team_name": "Knockout Home 3", "team_code": "K03", "points": 0, "alive": 1},
            {"player": "Dan", "team_slot": 1, "team_name": "Knockout Away 4", "team_code": "L04", "points": 0, "alive": 0},
            {"player": "Dan", "team_slot": 2, "team_name": "Knockout Home 4", "team_code": "K04", "points": 0, "alive": 1},
            {"player": "Eve", "team_slot": 1, "team_name": "Knockout Away 5", "team_code": "L05", "points": 0, "alive": 0},
            {"player": "Eve", "team_slot": 2, "team_name": "Knockout Home 5", "team_code": "K05", "points": 0, "alive": 1},
        ],
        standings_rows=[],
        matches_rows=matches_rows,
        now=datetime(2026, 7, 6, 7, 0, tzinfo=UTC),
    )

    section_map = {section.title: section for section in view.insight_sections}
    assert len(section_map["Latest Knockouts"].items) == 5
    assert len(section_map["Latest Results"].items) == 10


def test_draw_href_is_exposed_in_dashboard_view():
    view = build_dashboard_view(
        settings=StubSettings(),
        leaderboard_inputs=[
            {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
            {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1},
        ],
        standings_rows=[],
        matches_rows=[],
    )

    assert view.draw_href == "/draw/"


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
    assert view.leaderboard_rows[0].total_points == 60
    assert view.leaderboard_rows[1].total_points == 39
