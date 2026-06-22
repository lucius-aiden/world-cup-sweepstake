from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from .models import LeaderboardRow, MovementRecord

ALIVE_FILL = PatternFill(fill_type="solid", fgColor="C6EFCE")
ELIMINATED_FILL = PatternFill(fill_type="solid", fgColor="FFC7CE")


def build_leaderboard(rows: list[dict], previous_ranks: dict[str, int]) -> tuple[list[LeaderboardRow], list[MovementRecord]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["player"]].append(dict(row))

    leaderboard: list[LeaderboardRow] = []
    for player, teams in grouped.items():
        teams = sorted(teams, key=lambda item: item["team_name"])
        first, second = teams[0], teams[1]
        leaderboard.append(
            LeaderboardRow(
                player=player,
                team_1=first["team_name"],
                team_1_points=int(first["points"]),
                team_1_status=_status_label(bool(first["alive"])),
                team_2=second["team_name"],
                team_2_points=int(second["points"]),
                team_2_status=_status_label(bool(second["alive"])),
                total_points=int(first["points"]) + int(second["points"]),
                teams_alive=int(bool(first["alive"])) + int(bool(second["alive"])),
                rank=0,
            )
        )

    leaderboard.sort(key=lambda row: (-row.total_points, -row.teams_alive, row.player.lower()))
    ranked_rows: list[LeaderboardRow] = []
    movements: list[MovementRecord] = []
    for index, row in enumerate(leaderboard, start=1):
        ranked = LeaderboardRow(**{**row.__dict__, "rank": index})
        ranked_rows.append(ranked)
        previous_rank = previous_ranks.get(ranked.player)
        movements.append(
            MovementRecord(
                player=ranked.player,
                previous_rank=previous_rank,
                new_rank=index,
                delta_points=ranked.total_points,
            )
        )
    return ranked_rows, movements


def write_workbook(leaderboard: list[LeaderboardRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Leaderboard"

    headers = [
        "Rank",
        "Player",
        "Team 1",
        "Team 1 Points",
        "Team 1 Status",
        "Team 2",
        "Team 2 Points",
        "Team 2 Status",
        "Total Points",
        "Teams Alive",
    ]
    sheet.append(headers)

    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for row in leaderboard:
        sheet.append(
            [
                row.rank,
                row.player,
                row.team_1,
                row.team_1_points,
                row.team_1_status,
                row.team_2,
                row.team_2_points,
                row.team_2_status,
                row.total_points,
                row.teams_alive,
            ]
        )

    for data_row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
        _apply_status_fill(data_row[4], data_row[4].value)
        _apply_status_fill(data_row[7], data_row[7].value)

    sheet.freeze_panes = "A2"
    _autosize(sheet)
    workbook.save(output_path)


def _status_label(alive: bool) -> str:
    return "Alive" if alive else "Eliminated"


def _apply_status_fill(cell, value: str) -> None:
    cell.fill = ALIVE_FILL if value == "Alive" else ELIMINATED_FILL


def _autosize(sheet) -> None:
    for column in sheet.columns:
        width = max(len("" if cell.value is None else str(cell.value)) for cell in column) + 2
        sheet.column_dimensions[column[0].column_letter].width = width

