from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime

import requests

from .configuration import Settings
from .models import Match, TeamStanding
from .team_codes import resolve_team_code

LOGGER = logging.getLogger(__name__)


class FootballDataProvider(ABC):
    @abstractmethod
    def fetch_played_matches(self) -> list[Match]:
        raise NotImplementedError

    @abstractmethod
    def fetch_standings(self) -> list[TeamStanding]:
        raise NotImplementedError

    @abstractmethod
    def is_completed_status(self, status: str) -> bool:
        raise NotImplementedError


class FootballDataOrgProvider(FootballDataProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": settings.football_api_key})
        self.base_url = settings.football_api_base_url

    def fetch_played_matches(self) -> list[Match]:
        utc_now = datetime.now(UTC)
        date_to = utc_now.date()
        date_from = datetime(self.settings.season, 1, 1, tzinfo=UTC).date()
        payload = self._get(
            f"/competitions/{self.settings.competition_code}/matches",
            params={
                "dateFrom": date_from.isoformat(),
                "dateTo": date_to.isoformat(),
                "season": self.settings.season,
            },
        )
        return [self._to_match(item) for item in payload.get("matches", [])]

    def fetch_standings(self) -> list[TeamStanding]:
        payload = self._get(
            f"/competitions/{self.settings.competition_code}/standings",
            params={"season": self.settings.season},
        )
        standings: dict[str, TeamStanding] = {}
        for table_group in payload.get("standings", []):
            for entry in table_group.get("table", []):
                team = entry.get("team", {})
                team_name = team.get("name") or team.get("shortName") or "Unknown"
                team_code = resolve_team_code(team_name, team.get("tla"))
                standing = TeamStanding(
                    team_code=team_code,
                    team_name=team_name,
                    played=int(entry.get("playedGames", 0)),
                    won=int(entry.get("won", 0)),
                    drawn=int(entry.get("draw", 0)),
                    lost=int(entry.get("lost", 0)),
                    goals_for=int(entry.get("goalsFor", 0)),
                    goals_against=int(entry.get("goalsAgainst", 0)),
                    goal_difference=int(entry.get("goalDifference", 0)),
                    points=int(entry.get("points", 0)),
                    alive=self._infer_alive(entry),
                )
                standings[standing.team_code] = standing
        return sorted(standings.values(), key=lambda item: item.team_name)

    def is_completed_status(self, status: str) -> bool:
        return status in {"FINISHED", "FT", "AET", "PEN"}

    def _get(self, path: str, params: dict[str, object] | None = None) -> dict:
        response = self.session.get(
            f"{self.base_url}{path}",
            params=params,
            timeout=self.settings.football_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def _to_match(self, item: dict) -> Match:
        score = item.get("score", {})
        full_time = score.get("fullTime", {})
        winner = score.get("winner")
        return Match(
            match_id=str(item["id"]),
            home_team=item["homeTeam"]["name"],
            away_team=item["awayTeam"]["name"],
            home_score=full_time.get("home"),
            away_score=full_time.get("away"),
            status=item.get("status", "UNKNOWN"),
            match_date=datetime.fromisoformat(item["utcDate"].replace("Z", "+00:00")),
            stage=item.get("stage"),
            winner=winner,
        )

    def _infer_alive(self, entry: dict) -> bool:
        if entry.get("qualification"):
            text = str(entry["qualification"]).lower()
            if "eliminated" in text:
                return False
            if any(keyword in text for keyword in ("advance", "qualified", "playoff")):
                return True
        return True


def build_provider(settings: Settings) -> FootballDataProvider:
    provider_name = settings.football_provider.lower()
    if provider_name == "football_data":
        return FootballDataOrgProvider(settings)
    raise ValueError(f"Unsupported football provider: {settings.football_provider}")
