from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .career import Mentality, Position


class LeagueCreate(BaseModel):
    name: str = Field(min_length=3, max_length=80)


class JoinLeague(BaseModel):
    invite_code: str = Field(min_length=8, max_length=40)


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str


class MemberView(BaseModel):
    user_id: str
    display_name: str
    role: str
    status: str
    joined_at: datetime
    removed_at: datetime | None


class LeagueView(BaseModel):
    id: str
    name: str
    commissioner_user_id: str
    max_members: int
    active_member_count: int
    invite_enabled: bool
    invite_version: int
    members: list[MemberView]


class LeagueCreated(LeagueView):
    invite_code: str


class InviteRotated(BaseModel):
    league_id: str
    invite_code: str
    invite_version: int


class AuditEventView(BaseModel):
    id: str
    event_type: str
    actor_user_id: str
    subject_user_id: str | None
    detail: str
    created_at: datetime


class DraftPickCreate(BaseModel):
    player_id: str = Field(min_length=1, max_length=80)
    player_name: str = Field(min_length=1, max_length=120)


class DraftPickView(BaseModel):
    pick_number: int
    round_number: int
    user_id: str
    player_id: str
    player_name: str


class DraftStateView(BaseModel):
    id: str
    league_id: str
    status: str
    current_pick: int
    current_round: int
    seconds_per_pick: int
    current_user_id: str | None
    seat_order: list[str]
    picks: list[DraftPickView]


class CareerPlayerInput(BaseModel):
    player_id: str = Field(min_length=1, max_length=80)
    position: Position
    attack: float = Field(ge=0, le=100)
    defense: float = Field(ge=0, le=100)
    consecutive_starts: int = Field(default=0, ge=0)


class CareerTeamInput(BaseModel):
    team_id: str = Field(min_length=1, max_length=80)
    formation: str = Field(min_length=5, max_length=5)
    mentality: Mentality
    starters: list[CareerPlayerInput] = Field(min_length=11, max_length=11)


class CareerSimulationRequest(BaseModel):
    home: CareerTeamInput
    away: CareerTeamInput
    seed: int


class CareerSimulationResponse(BaseModel):
    home_team_id: str
    away_team_id: str
    home_goals: int
    away_goals: int
    home_expected_goals: float
    away_expected_goals: float
    outcome: str
    seed: int
    data_status: str
