from src.leaderboard import build_leaderboard


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
