from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ParticipantTeam:
    participant_name: str
    team_name: str
    team_code: str


@dataclass(frozen=True)
class Match:
    match_id: str
    home_team: str
    away_team: str
    home_team_code: Optional[str]
    away_team_code: Optional[str]
    home_score: Optional[int]
    away_score: Optional[int]
    status: str
    match_date: datetime
    stage: Optional[str] = None
    group: Optional[str] = None
    winner: Optional[str] = None


@dataclass(frozen=True)
class TeamStanding:
    team_code: str
    team_name: str
    group_name: Optional[str]
    group_position: Optional[int]
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    alive: bool = True
    qualification_status: Optional[str] = None


@dataclass(frozen=True)
class TeamOdds:
    team_code: str
    team_name: str
    decimal: float
    bookmaker: str | None = None
    last_update: datetime | None = None


@dataclass(frozen=True)
class LeaderboardRow:
    player: str
    team_1: str
    team_1_points: int
    team_1_status: str
    team_2: str
    team_2_points: int
    team_2_status: str
    total_points: int
    teams_alive: int
    rank: int


@dataclass(frozen=True)
class MovementRecord:
    player: str
    previous_rank: Optional[int]
    new_rank: int
    previous_points: Optional[int]
    current_points: int
    impacted_teams: tuple[str, ...] = ()
