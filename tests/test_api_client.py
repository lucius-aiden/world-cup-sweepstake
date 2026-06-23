from src.api_client import FootballDataOrgProvider
from src.configuration import Settings


def test_fetch_standings_uses_group_order_not_global_position(monkeypatch, tmp_path):
    settings = Settings(
        raw={
            "app": {"name": "world-cup-sweepstake"},
            "tournament": {"name": "FIFA World Cup 2026", "competition_code": "WC", "season": 2026},
            "football_api": {
                "provider": "football_data",
                "base_url": "https://example.com",
                "api_key_env": "FOOTBALL_DATA_API_KEY",
                "timeout_seconds": 30,
            },
            "storage": {
                "database_path": "data/test.db",
                "participants_csv": "config/participants.csv",
                "leaderboard_output": "output/leaderboard.xlsx",
                "site_output": "site",
            },
            "teams": {"notifier": "console"},
            "job": {},
        },
        root_dir=tmp_path,
    )
    provider = FootballDataOrgProvider.__new__(FootballDataOrgProvider)
    provider.settings = settings
    provider.base_url = "https://example.com"
    provider.session = None
    monkeypatch.setattr(
        provider,
        "_get",
        lambda path, params=None: {
            "standings": [
                {
                    "group": "Group A",
                    "table": [
                        {"position": 22, "playedGames": 2, "won": 2, "draw": 0, "lost": 0, "goalsFor": 7, "goalsAgainst": 0, "goalDifference": 7, "points": 6, "team": {"name": "Germany", "tla": "GER"}},
                        {"position": 27, "playedGames": 2, "won": 2, "draw": 0, "lost": 0, "goalsFor": 5, "goalsAgainst": 0, "goalDifference": 5, "points": 6, "team": {"name": "Argentina", "tla": "ARG"}},
                    ],
                }
            ]
        },
    )

    standings = provider.fetch_standings()

    assert standings[1].team_code == "GER"
    assert standings[1].group_position == 1
    assert standings[0].team_code == "ARG"
    assert standings[0].group_position == 2
