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
    home_score: Optional[int]
    away_score: Optional[int]
    status: str
    match_date: datetime
    stage: Optional[str] = None
    winner: Optional[str] = None


@dataclass(frozen=True)
class TeamStanding:
    team_code: str
    team_name: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    alive: bool = True


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
    delta_points: int

