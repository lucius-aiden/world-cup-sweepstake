from datetime import UTC, datetime

from src.configuration import Settings
from src.site import build_static_site


class StubProvider:
    def fetch_recent_matches(self):
        from src.models import Match

        return [
            Match(
                match_id="1",
                home_team="Brazil",
                away_team="Japan",
                home_score=2,
                away_score=1,
                status="FINISHED",
                match_date=datetime(2026, 6, 11, 18, 0, tzinfo=UTC),
                stage="GROUP_STAGE",
            )
        ]

    def fetch_standings(self):
        from src.models import TeamStanding

        return [
            TeamStanding("BRA", "Brazil", 3, 2, 0, 1, 5, 3, 2, 6, True),
            TeamStanding("JPN", "Japan", 3, 1, 0, 2, 3, 4, -1, 3, True),
            TeamStanding("PAN", "Panama", 3, 0, 1, 2, 1, 5, -4, 1, False),
            TeamStanding("MEX", "Mexico", 3, 2, 1, 0, 6, 2, 4, 7, True),
        ]

    def is_completed_status(self, status: str) -> bool:
        return status == "FINISHED"


def test_build_static_site_writes_pages_bundle(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "participants.csv").write_text(
        "Player,Team1,Team2\nAlice,Brazil,Panama\nBob,Japan,Mexico\n",
        encoding="utf-8",
    )

    settings = Settings(
        raw={
            "app": {"name": "world-cup-sweepstake"},
            "tournament": {"name": "FIFA World Cup 2026", "competition_code": "WC", "season": 2026},
            "football_api": {
                "provider": "football_data",
                "base_url": "https://example.com",
                "api_key_env": "FOOTBALL_DATA_API_KEY",
            },
            "storage": {
                "database_path": "data/test.db",
                "participants_csv": "config/participants.csv",
                "leaderboard_output": "output/leaderboard.xlsx",
                "site_output": "site",
            },
            "teams": {"notifier": "console"},
            "job": {"recent_matches_window_days": 7, "top_n_summary": 3},
        },
        root_dir=tmp_path,
    )

    monkeypatch.setattr("src.site.build_provider", lambda _: StubProvider())

    output_dir = build_static_site(settings)

    index_html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "FIFA World Cup 2026" in index_html
    assert "Alice" in index_html
    assert "Brazil 2-1 Japan" in index_html
    assert (output_dir / "static" / "styles.css").exists()
    assert (output_dir / ".nojekyll").exists()
