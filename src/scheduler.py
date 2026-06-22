from __future__ import annotations

import logging
from dataclasses import dataclass

from . import database
from .api_client import FootballDataProvider
from .configuration import Settings
from .leaderboard import build_leaderboard, write_workbook
from .models import LeaderboardRow, Match, MovementRecord
from .sharepoint import SharePointClient
from .team_codes import resolve_team_code
from .teams import TeamsNotifier

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunResult:
    processed_matches: int
    leaderboard: list[LeaderboardRow]


class SweepstakeService:
    def __init__(
        self,
        settings: Settings,
        provider: FootballDataProvider,
        notifier: TeamsNotifier,
        sharepoint_client: SharePointClient,
    ):
        self.settings = settings
        self.provider = provider
        self.notifier = notifier
        self.sharepoint_client = sharepoint_client

    def run_once(self) -> RunResult:
        connection = database.connect(self.settings.database_path)
        database.migrate(connection)
        database.import_participants(connection, self.settings.participants_csv)

        matches = self.provider.fetch_recent_matches()
        completed_matches = [match for match in matches if self.provider.is_completed_status(match.status)]
        changed_matches = database.upsert_matches(connection, completed_matches)

        standings = self.provider.fetch_standings()
        database.replace_team_standings(connection, standings)

        previous_ranks = database.fetch_rank_snapshot(connection)
        leaderboard, _ = build_leaderboard(database.fetch_leaderboard_inputs(connection), previous_ranks)
        write_workbook(leaderboard, self.settings.leaderboard_output)
        self.sharepoint_client.upload_leaderboard(self.settings.leaderboard_output)

        processed_count = 0
        for match in changed_matches:
            if not self.provider.is_completed_status(match.status):
                continue
            if database.was_posted(connection, match.match_id):
                continue
            affected_players = _affected_players(match, previous_ranks, leaderboard)
            self.notifier.post_match_update(match, affected_players, leaderboard)
            database.mark_posted(connection, match.match_id)
            processed_count += 1

        database.store_rank_snapshot(connection, leaderboard)
        LOGGER.info("Run complete. processed_matches=%s", processed_count)
        return RunResult(processed_matches=processed_count, leaderboard=leaderboard)


def _affected_players(
    match: Match,
    previous_ranks: dict[str, int],
    leaderboard: list[LeaderboardRow],
) -> list[MovementRecord]:
    impacted_teams = {resolve_team_code(match.home_team), resolve_team_code(match.away_team)}
    records: list[MovementRecord] = []
    for row in leaderboard:
        if resolve_team_code(row.team_1) not in impacted_teams and resolve_team_code(row.team_2) not in impacted_teams:
            continue
        records.append(
            MovementRecord(
                player=row.player,
                previous_rank=previous_ranks.get(row.player),
                new_rank=row.rank,
                delta_points=row.total_points,
            )
        )
    records.sort(key=lambda item: item.new_rank)
    return records
