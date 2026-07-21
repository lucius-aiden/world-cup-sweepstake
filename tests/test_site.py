from datetime import UTC, datetime

from src.configuration import Settings
from src.site import build_static_site


class StubProvider:
    def fetch_played_matches(self):
        from src.models import Match

        return [
            Match(
                match_id="1",
                home_team="Brazil",
                home_team_code="BRA",
                away_team="Japan",
                away_team_code="JPN",
                home_score=2,
                away_score=1,
                status="FINISHED",
                match_date=datetime(2026, 6, 23, 6, 30, tzinfo=UTC),
                stage="GROUP_STAGE",
                group="GROUP_A",
            ),
            Match(
                match_id="2",
                home_team="Brazil",
                home_team_code="BRA",
                away_team="Norway",
                away_team_code="NOR",
                home_score=None,
                away_score=None,
                status="TIMED",
                match_date=datetime(2026, 6, 23, 19, 0, tzinfo=UTC),
                stage="GROUP_STAGE",
                group="GROUP_A",
            ),
        ]

    def fetch_standings(self):
        from src.models import TeamStanding

        return [
            TeamStanding("BRA", "Brazil", "Group A", 1, 3, 2, 0, 1, 5, 3, 2, 6, True, "Qualified"),
            TeamStanding("JPN", "Japan", "Group A", 2, 3, 1, 0, 2, 3, 4, -1, 3, True, None),
            TeamStanding("PAN", "Panama", "Group A", 3, 3, 0, 1, 2, 1, 5, -4, 1, True, None),
            TeamStanding("MEX", "Mexico", "Group B", 1, 3, 2, 1, 0, 6, 2, 4, 7, True, "Qualified"),
        ]

    def fetch_top_scorers(self):
        from src.models import TopScorer

        return [
            TopScorer("Kylian Mbappe", "France", "FRA", 6, 2, 1),
            TopScorer("Vinicius Junior", "Brazil", "BRA", 4, 3, 0),
        ]

    def is_completed_status(self, status: str) -> bool:
        return status == "FINISHED"


def test_build_static_site_writes_two_page_bundle_and_daily_message(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "participants.csv").write_text(
        "Player,Team1,Team2\nAlice,Brazil,Panama\nBob,Japan,Mexico\n",
        encoding="utf-8",
    )

    settings = Settings(
        raw={
            "app": {"name": "world-cup-sweepstake", "timezone": "Europe/London"},
            "tournament": {"name": "FIFA World Cup 2026", "competition_code": "WC", "season": 2026},
            "football_api": {
                "provider": "football_data",
                "base_url": "https://example.com",
                "api_key_env": "FOOTBALL_DATA_API_KEY",
            },
            "odds_api": {"provider": "none"},
            "storage": {
                "database_path": "data/test.db",
                "participants_csv": "config/participants.csv",
                "leaderboard_output": "output/leaderboard.xlsx",
                "site_output": "site",
                "daily_messages_output": "outputs/daily_messages",
            },
            "teams": {"notifier": "console"},
            "job": {"recent_matches_window_days": 7, "top_n_summary": 3, "daily_message_hour": 7},
        },
        root_dir=tmp_path,
    )

    monkeypatch.setattr("src.site.build_provider", lambda _: StubProvider())

    output_dir = build_static_site(
        settings,
        now=datetime(2026, 6, 23, 6, 0, tzinfo=UTC),
    )

    index_html = (output_dir / "index.html").read_text(encoding="utf-8")
    leaderboard_html = (output_dir / "leaderboard" / "index.html").read_text(encoding="utf-8")
    daily_message = (tmp_path / "outputs" / "daily_messages" / "2026-06-23.txt").read_text(encoding="utf-8")

    assert "Insights" in index_html
    assert "Leaderboard" in leaderboard_html
    assert "Alice" in leaderboard_html
    assert "Pearson ELS Sweepstake" in index_html
    assert "Pearson ELS Sweepstake" in leaderboard_html
    assert "Official Scoreboard UI for ELS 2026 Football World Cup Sweepstake." in index_html
    assert 'class="panel insight-panel insight-panel-wide"' not in index_html
    assert 'href="./leaderboard/"' in index_html
    assert 'href="../"' in leaderboard_html
    assert 'href="./"' in leaderboard_html
    assert 'href="./static/styles.css"' in index_html
    assert 'href="../static/styles.css"' in leaderboard_html
    assert 'src="../static/leaderboard.js"' in leaderboard_html
    assert "How Scoring Works" in leaderboard_html
    assert "Each participant has two teams." in leaderboard_html
    assert "10 for the round of 32" in leaderboard_html
    assert "another 20 for the round of 16" in leaderboard_html
    assert "another 40 for semi-finals and the third-place playoff" in leaderboard_html
    assert "another 50 for the final" in leaderboard_html
    assert "Top Scorers" in index_html
    assert "Kylian Mbappe" in index_html
    assert "Top scorer" in leaderboard_html
    assert "Tournament win odds" not in leaderboard_html
    assert "Current leader:" in daily_message


def test_build_static_site_can_force_daily_message_outside_refresh_window(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "participants.csv").write_text(
        "Player,Team1,Team2\nAlice,Brazil,Panama\nBob,Japan,Mexico\n",
        encoding="utf-8",
    )

    settings = Settings(
        raw={
            "app": {"name": "world-cup-sweepstake", "timezone": "Europe/London"},
            "tournament": {"name": "FIFA World Cup 2026", "competition_code": "WC", "season": 2026},
            "football_api": {
                "provider": "football_data",
                "base_url": "https://example.com",
                "api_key_env": "FOOTBALL_DATA_API_KEY",
            },
            "odds_api": {"provider": "none"},
            "storage": {
                "database_path": "data/test.db",
                "participants_csv": "config/participants.csv",
                "leaderboard_output": "output/leaderboard.xlsx",
                "site_output": "site",
                "daily_messages_output": "outputs/daily_messages",
            },
            "teams": {"notifier": "console"},
            "job": {"recent_matches_window_days": 7, "top_n_summary": 3, "daily_message_hour": 7},
        },
        root_dir=tmp_path,
    )

    monkeypatch.setattr("src.site.build_provider", lambda _: StubProvider())

    build_static_site(
        settings,
        now=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        force_daily_report=True,
    )

    assert (tmp_path / "outputs" / "daily_messages" / "2026-06-23.txt").exists()
