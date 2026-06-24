import os
from datetime import UTC, datetime, timedelta

from src.configuration import Settings
from src.models import TeamOdds
from src.odds import _parse_the_odds_api_payload
from src.odds import TheOddsApiProvider


def test_odds_provider_keeps_shortest_decimal_price_per_team():
    payload = [
        {
            "bookmakers": [
                {
                    "title": "Book A",
                    "last_update": "2026-06-23T06:00:00Z",
                    "markets": [
                        {
                            "key": "outrights",
                            "outcomes": [
                                {"name": "Brazil", "price": 6.0},
                                {"name": "Japan", "price": 25.0},
                            ],
                        }
                    ],
                },
                {
                    "title": "Book B",
                    "last_update": "2026-06-23T06:05:00Z",
                    "markets": [
                        {
                            "key": "outrights",
                            "outcomes": [
                                {"name": "Brazil", "price": 5.5},
                            ],
                        }
                    ],
                },
            ]
        }
    ]

    odds = _parse_the_odds_api_payload(payload)

    assert odds["BRA"].decimal == 5.5
    assert odds["BRA"].bookmaker == "Book B"
    assert odds["JPN"].decimal == 25.0


def test_odds_provider_reuses_fresh_cache_without_network(monkeypatch, tmp_path):
    settings = Settings(
        raw={
            "app": {"name": "world-cup-sweepstake"},
            "tournament": {"name": "FIFA World Cup 2026", "competition_code": "WC", "season": 2026},
            "football_api": {"provider": "football_data", "base_url": "https://example.com", "api_key_env": "FOOTBALL_DATA_API_KEY"},
            "storage": {"database_path": "data/test.db", "participants_csv": "config/participants.csv", "leaderboard_output": "output/leaderboard.xlsx", "site_output": "site", "odds_cache_path": "data/odds_cache.json"},
            "odds_api": {"provider": "the_odds_api", "api_key_env": "THE_ODDS_API_KEY", "sport_key": "soccer_fifa_world_cup_winner", "refresh_hours": 6},
            "teams": {"notifier": "console"},
            "job": {},
        },
        root_dir=tmp_path,
    )
    provider = TheOddsApiProvider(settings)
    provider._store_cache_payload({"BRA": TeamOdds("BRA", "Brazil", 5.5)})
    monkeypatch.setenv("THE_ODDS_API_KEY", "test-key")
    provider.api_key = os.getenv("THE_ODDS_API_KEY")
    monkeypatch.setattr("src.odds.requests.get", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network should not run")))

    odds = provider.fetch_tournament_winner_odds()

    assert odds["BRA"].decimal == 5.5


def test_odds_provider_fetches_again_when_cache_is_stale(monkeypatch, tmp_path):
    settings = Settings(
        raw={
            "app": {"name": "world-cup-sweepstake"},
            "tournament": {"name": "FIFA World Cup 2026", "competition_code": "WC", "season": 2026},
            "football_api": {"provider": "football_data", "base_url": "https://example.com", "api_key_env": "FOOTBALL_DATA_API_KEY"},
            "storage": {"database_path": "data/test.db", "participants_csv": "config/participants.csv", "leaderboard_output": "output/leaderboard.xlsx", "site_output": "site", "odds_cache_path": "data/odds_cache.json"},
            "odds_api": {"provider": "the_odds_api", "api_key_env": "THE_ODDS_API_KEY", "sport_key": "soccer_fifa_world_cup_winner", "refresh_hours": 6},
            "teams": {"notifier": "console"},
            "job": {},
        },
        root_dir=tmp_path,
    )
    provider = TheOddsApiProvider(settings)
    provider._store_cache_payload({"BRA": TeamOdds("BRA", "Brazil", 6.0)})
    stale_time = (datetime.now(UTC) - timedelta(hours=7)).isoformat()
    cache_text = provider.cache_path.read_text(encoding="utf-8").replace(provider._load_cache_payload()["fetched_at"], stale_time)
    provider.cache_path.write_text(cache_text, encoding="utf-8")
    monkeypatch.setenv("THE_ODDS_API_KEY", "test-key")
    provider.api_key = os.getenv("THE_ODDS_API_KEY")

    class StubResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"bookmakers": [{"title": "Book", "last_update": "2026-06-23T06:00:00Z", "markets": [{"key": "outrights", "outcomes": [{"name": "Brazil", "price": 5.0}]}]}]}]

    monkeypatch.setattr("src.odds.requests.get", lambda *args, **kwargs: StubResponse())

    odds = provider.fetch_tournament_winner_odds()

    assert odds["BRA"].decimal == 5.0
