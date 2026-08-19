"""Pydantic request/response schemas, kept separate from the SQLAlchemy models."""

from pydantic import BaseModel


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
