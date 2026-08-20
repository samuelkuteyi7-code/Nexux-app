"""
Core data models for the NEXUS MVP.

Deliberately minimal, matching Master Spec section 19 (MVP scope):
profile -> one goal -> constrained world -> decisions -> simulation
state -> a few What If? branches.
"""

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class User(Base):
    """
    A real account - separate from UserProfile. This is identity
    (login credentials); UserProfile is the in-app goal/interests data
    tied to that identity. Kept separate so identity can later grow
    (email verification, OAuth, password reset) without touching the
    simulation-facing profile data.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    """
    Section 7.1 User Data - only the fields the MVP actually uses.
    Financial/CV data comes later with the Real-World Opportunity Engine.
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    background = Column(String, default="")
    education = Column(String, default="")
    interests = Column(JSON, default=list)      # list[str]
    goal = Column(String, nullable=False)        # single MVP goal, e.g. "become a software developer"

    user = relationship("User", back_populates="profile")
    worlds = relationship("World", back_populates="owner", cascade="all, delete-orphan")


class World(Base):
    """
    Section 8 Personalized World + Section 9 World State.

    `state` holds the mutable simulation state as JSON:
    {
        "time_step": 0,
        "resources": {"money": 1000, "energy": 100},
        "skills": {"coding": 10, "networking": 5},
        "relationships": {},
        "log": []                # human-readable event/decision history
    }
    Keeping state as one JSON blob keeps the MVP simple; split into
    proper tables once the shape stabilizes.
    """
    __tablename__ = "worlds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    goal = Column(String, nullable=False)
    state = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("UserProfile", back_populates="worlds")
    decisions = relationship("Decision", back_populates="world", cascade="all, delete-orphan")


class Decision(Base):
    """
    A single decision made inside a world and its resulting consequence.
    This is the simulation engine's audit trail (section 9).
    """
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)
    situation = Column(String, nullable=False)
    choice = Column(String, nullable=False)
    consequence = Column(String, nullable=False)
    state_delta = Column(JSON, default=dict)   # what changed numerically
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    world = relationship("World", back_populates="decisions")


class WhatIfBranch(Base):
    """
    Section 11 What If? Scenario Engine.

    A hypothetical projection that does NOT touch the real world state -
    it snapshots a projected outcome for comparison only.
    """
    __tablename__ = "whatif_branches"

    id = Column(Integer, primary_key=True, index=True)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)
    question = Column(String, nullable=False)          # "What if I learn programming for a year?"
    assumptions = Column(JSON, default=list)            # list[str], stated explicitly per spec section 11
    projected_state = Column(JSON, nullable=False)      # projected outcome, never merged into real state
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
