from src.leaderboard import build_leaderboard
from src.leaderboard_state import enrich_leaderboard_inputs


def test_leaderboard_sorting_and_alive_count():
    rows = [
        {"player": "Sarah", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
        {"player": "Sarah", "team_slot": 2, "team_name": "USA", "team_code": "USA", "points": 4, "alive": 1},
        {"player": "Tom", "team_slot": 1, "team_name": "England", "team_code": "ENG", "points": 5, "alive": 1},
        {"player": "Tom", "team_slot": 2, "team_name": "Japan", "team_code": "JPN", "points": 5, "alive": 0},
        {"player": "Mike", "team_slot": 1, "team_name": "Argentina", "team_code": "ARG", "points": 6, "alive": 1},
        {"player": "Mike", "team_slot": 2, "team_name": "Mexico", "team_code": "MEX", "points": 1, "alive": 1},
    ]

    leaderboard, movements = build_leaderboard(
        rows,
        previous_ranks={"Tom": 1, "Sarah": 2, "Mike": 3},
        previous_points={"Sarah": 7, "Tom": 8, "Mike": 6},
    )

    assert [row.player for row in leaderboard] == ["Sarah", "Tom", "Mike"]
    assert leaderboard[0].total_points == 10
    assert leaderboard[1].teams_alive == 1
    assert movements[0].previous_points == 7
    assert movements[0].current_points == 10


def test_leaderboard_uses_knockout_contribution_rules_when_enriched():
    rows = [
        {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 7, "alive": 0, "contributing_points": 0, "advancement_bonus": 0},
        {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 6, "alive": 1, "contributing_points": 6, "advancement_bonus": 3},
        {"player": "Bob", "team_slot": 1, "team_name": "Germany", "team_code": "GER", "points": 7, "alive": 1, "contributing_points": 7, "advancement_bonus": 2},
        {"player": "Bob", "team_slot": 2, "team_name": "Spain", "team_code": "ESP", "points": 5, "alive": 1, "contributing_points": 5, "advancement_bonus": 2},
        {"player": "Cara", "team_slot": 1, "team_name": "Japan", "team_code": "JPN", "points": 6, "alive": 0, "contributing_points": 0, "advancement_bonus": 0},
        {"player": "Cara", "team_slot": 2, "team_name": "Mexico", "team_code": "MEX", "points": 6, "alive": 0, "contributing_points": 0, "advancement_bonus": 0},
    ]

    leaderboard, _ = build_leaderboard(rows, previous_ranks={})

    assert [row.player for row in leaderboard] == ["Bob", "Alice", "Cara"]
    assert [row.total_points for row in leaderboard] == [16, 9, 0]


def test_leaderboard_ties_prefer_more_teams_alive_before_name_order():
    rows = [
        {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 5, "alive": 0},
        {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 5, "alive": 0},
        {"player": "Bob", "team_slot": 1, "team_name": "Germany", "team_code": "GER", "points": 6, "alive": 1},
        {"player": "Bob", "team_slot": 2, "team_name": "Spain", "team_code": "ESP", "points": 4, "alive": 0},
    ]

    leaderboard, _ = build_leaderboard(rows, previous_ranks={})

    assert [row.player for row in leaderboard] == ["Bob", "Alice"]


def test_leaderboard_normalizes_string_alive_flags():
    rows = [
        {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 5, "alive": "0"},
        {"player": "Alice", "team_slot": 2, "team_name": "France", "team_code": "FRA", "points": 5, "alive": "1"},
    ]

    leaderboard, _ = build_leaderboard(rows, previous_ranks={})

    assert leaderboard[0].team_1_status == "Knocked out"
    assert leaderboard[0].team_2_status == "Still in"
    assert leaderboard[0].teams_alive == 1


def test_enrich_leaderboard_inputs_marks_group_non_qualifiers_out_after_knockout():
    rows = [
        {"player": "Angela", "team_slot": 1, "team_name": "New Zealand", "team_code": "NZL", "points": 1, "alive": 1},
        {"player": "Angela", "team_slot": 2, "team_name": "South Korea", "team_code": "KOR", "points": 3, "alive": 1},
    ]
    standings_rows = [
        {"team_code": "NZL", "team_name": "New Zealand", "group_name": "Group G", "group_position": 4, "played": 3, "points": 1, "alive": 1, "qualification_status": None},
        {"team_code": "KOR", "team_name": "South Korea", "group_name": "Group A", "group_position": 3, "played": 3, "points": 3, "alive": 1, "qualification_status": None},
    ]
    matches_rows = [
        {
            "match_id": "1",
            "home_team": "Canada",
            "home_team_code": "CAN",
            "away_team": "South Africa",
            "away_team_code": "RSA",
            "home_score": 1,
            "away_score": 0,
            "status": "FINISHED",
            "match_date": "2026-06-29T12:00:00+00:00",
            "stage": "LAST_32",
            "winner": "HOME_TEAM",
        },
    ]

    leaderboard, _ = build_leaderboard(
        enrich_leaderboard_inputs(rows, standings_rows, matches_rows),
        previous_ranks={},
    )

    assert leaderboard[0].team_1_status == "Knocked out"
    assert leaderboard[0].team_2_status == "Knocked out"
    assert leaderboard[0].teams_alive == 0


def test_enrich_leaderboard_inputs_marks_missing_standings_teams_out_after_knockout():
    rows = [
        {"player": "Catriona", "team_slot": 1, "team_name": "Iran", "team_code": "IRN", "points": 3, "alive": 1},
        {"player": "Catriona", "team_slot": 2, "team_name": "Qatar", "team_code": "QAT", "points": 1, "alive": 1},
    ]
    matches_rows = [
        {
            "match_id": "1",
            "home_team": "Canada",
            "home_team_code": "CAN",
            "away_team": "South Africa",
            "away_team_code": "RSA",
            "home_score": 1,
            "away_score": 0,
            "status": "FINISHED",
            "match_date": "2026-06-29T12:00:00+00:00",
            "stage": "LAST_32",
            "winner": "HOME_TEAM",
        },
    ]

    leaderboard, _ = build_leaderboard(
        enrich_leaderboard_inputs(rows, standings_rows=[], matches_rows=matches_rows),
        previous_ranks={},
    )

    assert leaderboard[0].team_1_status == "Knocked out"
    assert leaderboard[0].team_2_status == "Knocked out"
    assert leaderboard[0].teams_alive == 0


def test_enrich_leaderboard_inputs_uses_group_matches_when_standings_are_missing():
    rows = [
        {"player": "Bob", "team_slot": 1, "team_name": "Belgium", "team_code": "BEL", "points": 2, "alive": 1},
        {"player": "Bob", "team_slot": 2, "team_name": "Iraq", "team_code": "IRQ", "points": 1, "alive": 1},
    ]
    matches_rows = [
        {
            "match_id": "g1",
            "home_team": "Belgium",
            "home_team_code": "BEL",
            "away_team": "Iraq",
            "away_team_code": "IRQ",
            "home_score": 1,
            "away_score": 1,
            "status": "FINISHED",
            "match_date": "2026-06-20T12:00:00+00:00",
            "stage": "GROUP_STAGE",
            "group_name": "GROUP_X",
            "winner": None,
        },
        {
            "match_id": "g2",
            "home_team": "Belgium",
            "home_team_code": "BEL",
            "away_team": "Canada",
            "away_team_code": "CAN",
            "home_score": 0,
            "away_score": 1,
            "status": "FINISHED",
            "match_date": "2026-06-23T12:00:00+00:00",
            "stage": "GROUP_STAGE",
            "group_name": "GROUP_X",
            "winner": "AWAY_TEAM",
        },
        {
            "match_id": "g3",
            "home_team": "Iraq",
            "home_team_code": "IRQ",
            "away_team": "Canada",
            "away_team_code": "CAN",
            "home_score": 0,
            "away_score": 2,
            "status": "FINISHED",
            "match_date": "2026-06-26T12:00:00+00:00",
            "stage": "GROUP_STAGE",
            "group_name": "GROUP_X",
            "winner": "AWAY_TEAM",
        },
        {
            "match_id": "g4",
            "home_team": "Belgium",
            "home_team_code": "BEL",
            "away_team": "Mexico",
            "away_team_code": "MEX",
            "home_score": 0,
            "away_score": 1,
            "status": "FINISHED",
            "match_date": "2026-06-27T12:00:00+00:00",
            "stage": "GROUP_STAGE",
            "group_name": "GROUP_X",
            "winner": "AWAY_TEAM",
        },
        {
            "match_id": "g5",
            "home_team": "Iraq",
            "home_team_code": "IRQ",
            "away_team": "Mexico",
            "away_team_code": "MEX",
            "home_score": 0,
            "away_score": 1,
            "status": "FINISHED",
            "match_date": "2026-06-28T12:00:00+00:00",
            "stage": "GROUP_STAGE",
            "group_name": "GROUP_X",
            "winner": "AWAY_TEAM",
        },
        {
            "match_id": "k1",
            "home_team": "Canada",
            "home_team_code": "CAN",
            "away_team": "South Africa",
            "away_team_code": "RSA",
            "home_score": 1,
            "away_score": 0,
            "status": "FINISHED",
            "match_date": "2026-06-29T12:00:00+00:00",
            "stage": "LAST_32",
            "winner": "HOME_TEAM",
        },
    ]

    leaderboard, _ = build_leaderboard(
        enrich_leaderboard_inputs(rows, standings_rows=[], matches_rows=matches_rows),
        previous_ranks={},
    )

    assert leaderboard[0].team_1_status == "Knocked out"
    assert leaderboard[0].team_2_status == "Knocked out"
    assert leaderboard[0].teams_alive == 0
