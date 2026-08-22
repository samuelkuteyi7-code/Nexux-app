"""Pydantic request/response schemas, kept separate from the SQLAlchemy models."""

from datetime import date
from pydantic import BaseModel, EmailStr, field_validator


class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str
    date_of_birth: date | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileCreate(BaseModel):
    name: str
    background: str = ""
    education: str = ""
    interests: list[str] = []
    goal: str


class ProfileOut(BaseModel):
    id: int
    name: str
    background: str
    education: str
    interests: list[str]
    goal: str

    class Config:
        from_attributes = True


class WorldOut(BaseModel):
    id: int
    user_id: int
    goal: str
    state: dict

    class Config:
        from_attributes = True


class DecisionChoice(BaseModel):
    world_id: int
    situation: str
    choice_key: str
    option_effects: dict


class DecisionOut(BaseModel):
    id: int
    world_id: int
    situation: str
    choice: str
    consequence: str
    state_delta: dict
    xp_earned: int = 0

    class Config:
        from_attributes = True


class WhatIfRequest(BaseModel):
    world_id: int
    question: str
    assumptions: list[str] = []
    hypothetical_effects: dict
    steps: int = 1


class WhatIfOut(BaseModel):
    id: int
    world_id: int
    question: str
    assumptions: list[str]
    projected_state: dict

    class Config:
        from_attributes = True


class GameProfileOut(BaseModel):
    level: int
    xp_total: int
    xp_into_level: int
    xp_for_next_level: int
    progress_pct: int
    streak_count: int
class MissionOut(BaseModel):
    key: str
    title: str
    description: str
    reward_xp: int
    current: int
    target: int
    progress_pct: int
    completed: bool
    claimed: bool


class MissionClaimResult(BaseModel):
    mission: MissionOut
    game: GameProfileOut
class DailyChallengeOut(BaseModel):
    key: str
    title: str
    description: str
    reward_xp: int
    current: int
    target: int
    progress_pct: int
    completed: bool
    claimed: bool


class DailyChallengeClaimResult(BaseModel):
    challenge: DailyChallengeOut
    game: GameProfileOut
