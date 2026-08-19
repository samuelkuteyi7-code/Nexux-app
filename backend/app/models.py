"""
Core data models for the NEXUS MVP.

Deliberately minimal, matching Master Spec section 19 (MVP scope):
profile -> one goal -> constrained world -> decisions -> simulation
state -> a few What If? branches.
"""

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    background = Column(String, default="")
    education = Column(String, default="")
    interests = Column(JSON, default=list)
    goal = Column(String, nullable=False)

    worlds = relationship("World", back_populates="owner", cascade="all, delete-orphan")


class World(Base):
    __tablename__ = "worlds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    goal = Column(String, nullable=False)
    state = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("UserProfile", back_populates="worlds")
    decisions = relationship("Decision", back_populates="world", cascade="all, delete-orphan")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)
    situation = Column(String, nullable=False)
    choice = Column(String, nullable=False)
    consequence = Column(String, nullable=False)
    state_delta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="decisions")


class WhatIfBranch(Base):
    __tablename__ = "whatif_branches"

    id = Column(Integer, primary_key=True, index=True)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)
    question = Column(String, nullable=False)
    assumptions = Column(JSON, default=list)
    projected_state = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
