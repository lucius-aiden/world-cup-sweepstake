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


def test_fetch_standings_prefers_group_tables_over_overall_table(monkeypatch, tmp_path):
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
                    "type": "TOTAL",
                    "table": [
                        {"position": 22, "playedGames": 2, "won": 2, "draw": 0, "lost": 0, "goalsFor": 7, "goalsAgainst": 0, "goalDifference": 7, "points": 6, "team": {"name": "Germany", "tla": "GER"}},
                    ],
                },
                {
                    "group": "Group A",
                    "table": [
                        {"position": 99, "playedGames": 2, "won": 2, "draw": 0, "lost": 0, "goalsFor": 7, "goalsAgainst": 0, "goalDifference": 7, "points": 6, "team": {"name": "Germany", "tla": "GER"}},
                    ],
                },
            ]
        },
    )

    standings = provider.fetch_standings()

    assert standings[0].group_name == "Group A"
    assert standings[0].group_position == 1


def test_fetch_played_matches_preserves_penalty_shootout_breakdown(monkeypatch, tmp_path):
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
            "matches": [
                {
                    "id": 7,
                    "homeTeam": {"name": "England", "tla": "ENG"},
                    "awayTeam": {"name": "Japan", "tla": "JPN"},
                    "utcDate": "2026-07-04T18:00:00Z",
                    "status": "PEN",
                    "stage": "QUARTER_FINALS",
                    "group": None,
                    "score": {
                        "winner": "HOME_TEAM",
                        "duration": "PENALTY_SHOOTOUT",
                        "fullTime": {"home": 5, "away": 4},
                        "regularTime": {"home": 1, "away": 1},
                        "extraTime": {"home": 0, "away": 0},
                        "penalties": {"home": 4, "away": 3},
                    },
                }
            ]
        },
    )

    matches = provider.fetch_played_matches()

    assert len(matches) == 1
    assert matches[0].score_duration == "PENALTY_SHOOTOUT"
    assert matches[0].regular_home_score == 1
    assert matches[0].regular_away_score == 1
    assert matches[0].extra_home_score == 0
    assert matches[0].extra_away_score == 0
    assert matches[0].penalty_home_score == 4
    assert matches[0].penalty_away_score == 3
