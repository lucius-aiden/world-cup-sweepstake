from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import LeaderboardRow, Match, TeamStanding
from .team_codes import resolve_team_code


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS participant_teams (
        participant_id INTEGER NOT NULL,
        team_slot INTEGER NOT NULL,
        team_code TEXT NOT NULL,
        team_name TEXT NOT NULL,
        UNIQUE(participant_id, team_slot),
        FOREIGN KEY(participant_id) REFERENCES participants(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS matches (
        match_id TEXT PRIMARY KEY,
        home_team TEXT NOT NULL,
        home_team_code TEXT,
        away_team TEXT NOT NULL,
        away_team_code TEXT,
        home_score INTEGER,
        away_score INTEGER,
        status TEXT NOT NULL,
        match_date TEXT NOT NULL,
        posted_to_teams INTEGER NOT NULL DEFAULT 0,
        processed_at TEXT,
        stage TEXT,
        winner TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS team_standings (
        team_code TEXT PRIMARY KEY,
        team_name TEXT NOT NULL,
        group_name TEXT,
        group_position INTEGER,
        played INTEGER NOT NULL,
        won INTEGER NOT NULL,
        drawn INTEGER NOT NULL,
        lost INTEGER NOT NULL,
        goals_for INTEGER NOT NULL,
        goals_against INTEGER NOT NULL,
        goal_difference INTEGER NOT NULL,
        points INTEGER NOT NULL,
        alive INTEGER NOT NULL,
        qualification_status TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS job_state (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
]


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def migrate(connection: sqlite3.Connection) -> None:
    with connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(participant_teams)").fetchall()
        }
        if "team_slot" not in columns:
            connection.execute("ALTER TABLE participant_teams ADD COLUMN team_slot INTEGER")
            connection.execute(
                """
                UPDATE participant_teams
                SET team_slot = CASE
                    WHEN rowid IN (
                        SELECT MIN(rowid)
                        FROM participant_teams pt2
                        WHERE pt2.participant_id = participant_teams.participant_id
                    ) THEN 1
                    ELSE 2
                END
                """
            )
        match_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(matches)").fetchall()
        }
        if "home_team_code" not in match_columns:
            connection.execute("ALTER TABLE matches ADD COLUMN home_team_code TEXT")
        if "away_team_code" not in match_columns:
            connection.execute("ALTER TABLE matches ADD COLUMN away_team_code TEXT")
        standing_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(team_standings)").fetchall()
        }
        if "group_name" not in standing_columns:
            connection.execute("ALTER TABLE team_standings ADD COLUMN group_name TEXT")
        if "group_position" not in standing_columns:
            connection.execute("ALTER TABLE team_standings ADD COLUMN group_position INTEGER")
        if "qualification_status" not in standing_columns:
            connection.execute("ALTER TABLE team_standings ADD COLUMN qualification_status TEXT")


def import_participants(connection: sqlite3.Connection, participants_csv: Path) -> None:
    with participants_csv.open("r", encoding="utf-8", newline="") as handle, connection:
        reader = csv.DictReader(handle)
        connection.execute("DELETE FROM participant_teams")
        connection.execute("DELETE FROM participants")
        for row in reader:
            name = row["Player"].strip()
            participant_id = connection.execute(
                "INSERT INTO participants(name) VALUES (?)",
                (name,),
            ).lastrowid
            for slot, column in enumerate(("Team1", "Team2"), start=1):
                team_name = row[column].strip()
                team_code = normalize_team_code(team_name)
                connection.execute(
                    """
                    INSERT INTO participant_teams(participant_id, team_slot, team_code, team_name)
                    VALUES (?, ?, ?, ?)
                    """,
                    (participant_id, slot, team_code, team_name),
                )


def normalize_team_code(team_name: str) -> str:
    return resolve_team_code(team_name)


def upsert_matches(connection: sqlite3.Connection, matches: Iterable[Match]) -> list[Match]:
    newly_completed: list[Match] = []
    with connection:
        for match in matches:
            existing = connection.execute(
                "SELECT status FROM matches WHERE match_id = ?",
                (match.match_id,),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO matches(
                    match_id, home_team, home_team_code, away_team, away_team_code, home_score, away_score,
                    status, match_date, stage, winner
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(match_id) DO UPDATE SET
                    home_team=excluded.home_team,
                    home_team_code=excluded.home_team_code,
                    away_team=excluded.away_team,
                    away_team_code=excluded.away_team_code,
                    home_score=excluded.home_score,
                    away_score=excluded.away_score,
                    status=excluded.status,
                    match_date=excluded.match_date,
                    stage=excluded.stage,
                    winner=excluded.winner
                """,
                (
                    match.match_id,
                    match.home_team,
                    match.home_team_code,
                    match.away_team,
                    match.away_team_code,
                    match.home_score,
                    match.away_score,
                    match.status,
                    match.match_date.isoformat(),
                    match.stage,
                    match.winner,
                ),
            )
            if existing is None or existing["status"] != match.status:
                newly_completed.append(match)
    return newly_completed


def replace_team_standings(connection: sqlite3.Connection, standings: Iterable[TeamStanding]) -> None:
    with connection:
        connection.execute("DELETE FROM team_standings")
        connection.executemany(
            """
            INSERT INTO team_standings(
                team_code, team_name, group_name, group_position, played, won, drawn, lost,
                goals_for, goals_against, goal_difference, points, alive, qualification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    standing.team_code,
                    standing.team_name,
                    standing.group_name,
                    standing.group_position,
                    standing.played,
                    standing.won,
                    standing.drawn,
                    standing.lost,
                    standing.goals_for,
                    standing.goals_against,
                    standing.goal_difference,
                    standing.points,
                    int(standing.alive),
                    standing.qualification_status,
                )
                for standing in standings
            ],
        )


def fetch_leaderboard_inputs(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            p.name AS player,
            pt.team_slot,
            pt.team_name,
            pt.team_code,
            COALESCE(ts.points, 0) AS points,
            COALESCE(ts.alive, 1) AS alive
        FROM participants p
        JOIN participant_teams pt ON pt.participant_id = p.id
        LEFT JOIN team_standings ts ON ts.team_code = pt.team_code
        ORDER BY p.name ASC, pt.team_slot ASC
        """
    ).fetchall()


def fetch_rank_snapshot(connection: sqlite3.Connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT key, value
        FROM job_state
        WHERE key LIKE 'rank:%'
        """
    ).fetchall()
    return {row["key"].split(":", 1)[1]: int(row["value"]) for row in rows}


def fetch_points_snapshot(connection: sqlite3.Connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT key, value
        FROM job_state
        WHERE key LIKE 'points:%'
        """
    ).fetchall()
    return {row["key"].split(":", 1)[1]: int(row["value"]) for row in rows}


def get_job_state(connection: sqlite3.Connection, key: str) -> str | None:
    row = connection.execute("SELECT value FROM job_state WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    return str(row["value"])


def set_job_state(connection: sqlite3.Connection, key: str, value: str) -> None:
    with connection:
        connection.execute(
            """
            INSERT INTO job_state(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (key, value),
        )


def store_rank_snapshot(connection: sqlite3.Connection, leaderboard: list[LeaderboardRow]) -> None:
    with connection:
        connection.execute("DELETE FROM job_state WHERE key LIKE 'rank:%'")
        connection.execute("DELETE FROM job_state WHERE key LIKE 'points:%'")
        connection.executemany(
            "INSERT INTO job_state(key, value) VALUES (?, ?)",
            [(f"rank:{row.player}", str(row.rank)) for row in leaderboard],
        )
        connection.executemany(
            "INSERT INTO job_state(key, value) VALUES (?, ?)",
            [(f"points:{row.player}", str(row.total_points)) for row in leaderboard],
        )


def fetch_latest_completed_match(connection: sqlite3.Connection) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT match_id, home_team, home_team_code, away_team, away_team_code, home_score, away_score, match_date, stage, winner
        FROM matches
        WHERE status IN ('FINISHED', 'FT', 'AET', 'PEN')
        ORDER BY match_date DESC
        LIMIT 1
        """
    ).fetchone()


def fetch_all_matches(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            match_id,
            home_team,
            home_team_code,
            away_team,
            away_team_code,
            home_score,
            away_score,
            status,
            match_date,
            stage,
            winner
        FROM matches
        ORDER BY match_date ASC, match_id ASC
        """
    ).fetchall()


def fetch_team_standings(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            team_code,
            team_name,
            group_name,
            group_position,
            played,
            won,
            drawn,
            lost,
            goals_for,
            goals_against,
            goal_difference,
            points,
            alive,
            qualification_status
        FROM team_standings
        ORDER BY points DESC, goal_difference DESC, goals_for DESC, team_name ASC
        """
    ).fetchall()


def mark_posted(connection: sqlite3.Connection, match_id: str) -> None:
    with connection:
        connection.execute(
            "UPDATE matches SET posted_to_teams = 1 WHERE match_id = ?",
            (match_id,),
        )


def was_posted(connection: sqlite3.Connection, match_id: str) -> bool:
    row = connection.execute(
        "SELECT posted_to_teams FROM matches WHERE match_id = ?",
        (match_id,),
    ).fetchone()
    return bool(row and row["posted_to_teams"])
