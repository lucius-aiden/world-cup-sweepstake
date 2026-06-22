from __future__ import annotations

import logging
from typing import Protocol

import requests

from .configuration import Settings
from .models import LeaderboardRow, Match, MovementRecord

LOGGER = logging.getLogger(__name__)


class TeamsNotifier(Protocol):
    def post_match_update(
        self,
        match: Match,
        affected_players: list[MovementRecord],
        leaderboard: list[LeaderboardRow],
    ) -> None:
        ...


class ConsoleNotifier:
    def __init__(self, settings: Settings):
        self.top_n_summary = settings.top_n_summary

    def post_match_update(
        self,
        match: Match,
        affected_players: list[MovementRecord],
        leaderboard: list[LeaderboardRow],
    ) -> None:
        LOGGER.info("\n%s", render_message(match, affected_players, leaderboard, self.top_n_summary))


class IncomingWebhookNotifier:
    def __init__(self, settings: Settings):
        webhook_url = settings.graph_value("teams", "webhook_url_env")
        if not webhook_url:
            raise RuntimeError("TEAMS_WEBHOOK_URL is required for incoming webhook notifications.")
        self.webhook_url = webhook_url
        self.top_n_summary = settings.top_n_summary

    def post_match_update(
        self,
        match: Match,
        affected_players: list[MovementRecord],
        leaderboard: list[LeaderboardRow],
    ) -> None:
        message = render_message(match, affected_players, leaderboard, self.top_n_summary)
        response = requests.post(self.webhook_url, json={"text": message}, timeout=30)
        response.raise_for_status()


def build_notifier(settings: Settings) -> TeamsNotifier:
    notifier = settings.teams_notifier.lower()
    if notifier == "console":
        return ConsoleNotifier(settings)
    if notifier == "incoming_webhook":
        return IncomingWebhookNotifier(settings)
    raise ValueError(f"Unsupported teams notifier: {settings.teams_notifier}")


def render_message(
    match: Match,
    affected_players: list[MovementRecord],
    leaderboard: list[LeaderboardRow],
    top_n_summary: int,
) -> str:
    header = "🏁 FULL TIME"
    score_line = f"{match.home_team} {match.home_score}-{match.away_score} {match.away_team}"
    affected_lines = ["🎯 Affected players"]
    if affected_players:
        for record in affected_players:
            if record.previous_rank is None:
                movement = f"entered at #{record.new_rank}"
            elif record.previous_rank > record.new_rank:
                movement = f"up {record.previous_rank - record.new_rank} to #{record.new_rank}"
            elif record.previous_rank < record.new_rank:
                movement = f"down {record.new_rank - record.previous_rank} to #{record.new_rank}"
            else:
                movement = f"stayed at #{record.new_rank}"
            affected_lines.append(f"- {record.player}: {movement}")
    else:
        affected_lines.append("- No participant teams were involved in this match.")

    podium_lines = ["🏆 Top players"]
    for row in leaderboard[:top_n_summary]:
        podium_lines.append(f"- #{row.rank} {row.player}: {row.total_points} pts")

    return "\n".join([header, "", score_line, "", *affected_lines, "", *podium_lines])

