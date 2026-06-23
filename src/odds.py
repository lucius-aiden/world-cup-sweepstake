from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import requests

from .configuration import Settings
from .models import TeamOdds
from .team_codes import resolve_team_code

LOGGER = logging.getLogger(__name__)


class OddsProvider(ABC):
    @abstractmethod
    def fetch_tournament_winner_odds(self) -> dict[str, TeamOdds]:
        raise NotImplementedError


class NullOddsProvider(OddsProvider):
    def fetch_tournament_winner_odds(self) -> dict[str, TeamOdds]:
        return {}


class TheOddsApiProvider(OddsProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = os.getenv(str(settings.raw.get("odds_api", {}).get("api_key_env", "")))
        self.sport_key = settings.raw.get("odds_api", {}).get("sport_key")
        self.base_url = str(settings.raw.get("odds_api", {}).get("base_url", "https://api.the-odds-api.com/v4")).rstrip("/")
        self.regions = str(settings.raw.get("odds_api", {}).get("regions", "uk"))
        self.odds_format = str(settings.raw.get("odds_api", {}).get("odds_format", "decimal"))
        self.timeout_seconds = int(settings.raw.get("odds_api", {}).get("timeout_seconds", 20))

    def fetch_tournament_winner_odds(self) -> dict[str, TeamOdds]:
        if not self.api_key or not self.sport_key:
            return {}
        response = requests.get(
            f"{self.base_url}/sports/{self.sport_key}/odds",
            params={
                "apiKey": self.api_key,
                "regions": self.regions,
                "markets": "outrights",
                "oddsFormat": self.odds_format,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            return {}
        return _parse_the_odds_api_payload(payload)


def build_odds_provider(settings: Settings) -> OddsProvider:
    provider_name = str(settings.raw.get("odds_api", {}).get("provider", "none")).lower()
    if provider_name in {"", "none", "null"}:
        return NullOddsProvider()
    if provider_name == "the_odds_api":
        return TheOddsApiProvider(settings)
    raise ValueError(f"Unsupported odds provider: {provider_name}")


def _parse_the_odds_api_payload(payload: list[dict[str, Any]]) -> dict[str, TeamOdds]:
    by_team: dict[str, TeamOdds] = {}
    for event in payload:
        for bookmaker in event.get("bookmakers", []):
            bookmaker_title = bookmaker.get("title")
            last_update = _parse_datetime(bookmaker.get("last_update"))
            for market in bookmaker.get("markets", []):
                if market.get("key") != "outrights":
                    continue
                for outcome in market.get("outcomes", []):
                    if "price" not in outcome or outcome.get("name") is None:
                        continue
                    team_name = str(outcome["name"])
                    team_code = resolve_team_code(team_name)
                    price = float(outcome["price"])
                    existing = by_team.get(team_code)
                    if existing and existing.decimal <= price:
                        continue
                    by_team[team_code] = TeamOdds(
                        team_code=team_code,
                        team_name=team_name,
                        decimal=price,
                        bookmaker=bookmaker_title,
                        last_update=last_update,
                    )
    return by_team


def _parse_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        LOGGER.debug("Unable to parse odds timestamp: %s", value)
        return None
