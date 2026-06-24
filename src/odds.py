from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from pathlib import Path
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
        self.refresh_hours = int(settings.raw.get("odds_api", {}).get("refresh_hours", 6))
        self.cache_path = settings.odds_cache_path

    def fetch_tournament_winner_odds(self) -> dict[str, TeamOdds]:
        if not self.api_key or not self.sport_key:
            return self._load_cached_odds() or {}

        cached = self._load_cache_payload()
        if cached and not self._cache_expired(cached):
            return _deserialize_odds(cached.get("odds", {}))

        try:
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
                return self._load_cached_odds() or {}
            odds = _parse_the_odds_api_payload(payload)
            self._store_cache_payload(odds)
            return odds
        except requests.RequestException:
            LOGGER.exception("Failed to fetch odds, falling back to cache")
            return self._load_cached_odds() or {}

    def _load_cached_odds(self) -> dict[str, TeamOdds] | None:
        payload = self._load_cache_payload()
        if not payload:
            return None
        return _deserialize_odds(payload.get("odds", {}))

    def _load_cache_payload(self) -> dict[str, Any] | None:
        if not self.cache_path.exists():
            return None
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            LOGGER.exception("Failed to read odds cache")
            return None

    def _store_cache_payload(self, odds: dict[str, TeamOdds]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetched_at": datetime.now(UTC).isoformat(),
            "odds": {
                code: {
                    "team_code": item.team_code,
                    "team_name": item.team_name,
                    "decimal": item.decimal,
                    "bookmaker": item.bookmaker,
                    "last_update": item.last_update.isoformat() if item.last_update else None,
                }
                for code, item in odds.items()
            },
        }
        self.cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _cache_expired(self, payload: dict[str, Any]) -> bool:
        fetched_at = _parse_datetime(payload.get("fetched_at"))
        if fetched_at is None:
            return True
        return datetime.now(UTC) - fetched_at >= timedelta(hours=self.refresh_hours)


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


def _deserialize_odds(payload: dict[str, Any]) -> dict[str, TeamOdds]:
    odds: dict[str, TeamOdds] = {}
    for team_code, item in payload.items():
        odds[team_code] = TeamOdds(
            team_code=str(item["team_code"]),
            team_name=str(item["team_name"]),
            decimal=float(item["decimal"]),
            bookmaker=item.get("bookmaker"),
            last_update=_parse_datetime(item.get("last_update")),
        )
    return odds


def _parse_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        LOGGER.debug("Unable to parse odds timestamp: %s", value)
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
