from __future__ import annotations

import logging
from dataclasses import dataclass

from . import database
from .api_client import FootballDataProvider
from .configuration import Settings
from .leaderboard import build_leaderboard, write_workbook
from .leaderboard_state import enrich_leaderboard_inputs
from .models import LeaderboardRow, Match, MovementRecord
from .sharepoint import SharePointClient
from .standings import build_effective_standings
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

        matches = self.provider.fetch_played_matches()
        completed_matches = [match for match in matches if self.provider.is_completed_status(match.status)]
        changed_matches = database.upsert_matches(connection, completed_matches)

        standings = build_effective_standings(completed_matches, self.provider.fetch_standings())
        database.replace_team_standings(connection, standings)

        previous_ranks = database.fetch_rank_snapshot(connection)
        previous_points = database.fetch_points_snapshot(connection)
        leaderboard_inputs = enrich_leaderboard_inputs(
            [dict(row) for row in database.fetch_leaderboard_inputs(connection)],
            [dict(row) for row in database.fetch_team_standings(connection)],
            [dict(row) for row in database.fetch_all_matches(connection)],
        )
        leaderboard, _ = build_leaderboard(
            leaderboard_inputs,
            previous_ranks,
            previous_points,
        )
        write_workbook(leaderboard, self.settings.leaderboard_output)
        self.sharepoint_client.upload_leaderboard(self.settings.leaderboard_output)

        processed_count = 0
        for match in changed_matches:
            if not self.provider.is_completed_status(match.status):
                continue
            if database.was_posted(connection, match.match_id):
                continue
            affected_players = _affected_players(match, previous_ranks, leaderboard, previous_points)
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
    previous_points: dict[str, int] | None = None,
) -> list[MovementRecord]:
    previous_points = previous_points or {}
    impacted_teams = {
        resolve_team_code(match.home_team, match.home_team_code),
        resolve_team_code(match.away_team, match.away_team_code),
    }
    records: list[MovementRecord] = []
    for row in leaderboard:
        row_impacted = tuple(
            team_name
            for team_name in (row.team_1, row.team_2)
            if resolve_team_code(team_name) in impacted_teams
        )
        if not row_impacted:
            continue
        records.append(
            MovementRecord(
                player=row.player,
                previous_rank=previous_ranks.get(row.player),
                new_rank=row.rank,
                previous_points=previous_points.get(row.player),
                current_points=row.total_points,
                impacted_teams=row_impacted,
            )
        )
    records.sort(key=lambda item: item.new_rank)
    return records
