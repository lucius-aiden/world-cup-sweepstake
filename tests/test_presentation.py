from src.presentation import build_dashboard_view


class StubSettings:
    raw = {"tournament": {"name": "FIFA World Cup 2026"}}


def test_dashboard_view_builds_ranked_table_rows():
    inputs = [
        {"player": "Alice", "team_slot": 1, "team_name": "Brazil", "team_code": "BRA", "points": 6, "alive": 1},
        {"player": "Alice", "team_slot": 2, "team_name": "Panama", "team_code": "PAN", "points": 1, "alive": 0},
        {"player": "Bob", "team_slot": 1, "team_name": "Japan", "team_code": "JPN", "points": 3, "alive": 1},
        {"player": "Bob", "team_slot": 2, "team_name": "Mexico", "team_code": "MEX", "points": 3, "alive": 1},
    ]

    view = build_dashboard_view(StubSettings(), inputs)

    assert view.tournament_name == "FIFA World Cup 2026"
    assert [row.player for row in view.table_rows] == ["Alice", "Bob"]
    assert view.table_rows[0].team_1.flag == "🇧🇷"
    assert view.table_rows[0].total_points == 7
