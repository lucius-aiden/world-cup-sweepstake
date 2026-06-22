from src.leaderboard import build_leaderboard


def test_leaderboard_sorting_and_alive_count():
    rows = [
        {"player": "Sarah", "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
        {"player": "Sarah", "team_name": "USA", "team_code": "USA", "points": 4, "alive": 1},
        {"player": "Tom", "team_name": "England", "team_code": "ENG", "points": 5, "alive": 1},
        {"player": "Tom", "team_name": "Japan", "team_code": "JPN", "points": 5, "alive": 0},
        {"player": "Mike", "team_name": "Argentina", "team_code": "ARG", "points": 6, "alive": 1},
        {"player": "Mike", "team_name": "Mexico", "team_code": "MEX", "points": 1, "alive": 1},
    ]

    leaderboard, _ = build_leaderboard(rows, previous_ranks={"Tom": 1, "Sarah": 2, "Mike": 3})

    assert [row.player for row in leaderboard] == ["Sarah", "Tom", "Mike"]
    assert leaderboard[0].total_points == 10
    assert leaderboard[1].teams_alive == 1

