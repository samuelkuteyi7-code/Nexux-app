"""
Core data models for the NEXUS MVP.

Deliberately minimal, matching Master Spec section 19 (MVP scope):
profile -> one goal -> constrained world -> decisions -> simulation
state -> a few What If? branches. No opportunity engine, no social
layer, no complex economy yet - those are later phases.
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


class GameProfile(Base):
    """
    Section 15 Game Layer - "Interaction, missions, progression and
    rewards." Kept as its own table, separate from UserProfile
    (identity/goal data) and World (simulation state), matching the
    architecture principle that AI, simulation, and game-layer
    concerns stay decoupled. Missions land here too as they're built.

    Only `xp` is stored - level and progress-into-level are always
    derived from it (see app/game/leveling.py) so they can never
    drift out of sync.

    streak_count / last_checkin_date track daily check-ins (see
    app/game/streak.py). Dates are UTC calendar days - a streak can
    tick over at a slightly different local time than the user's own
    midnight, which is an accepted simplification for the MVP.
    """
    __tablename__ = "game_profiles"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), unique=True, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    streak_count = Column(Integer, default=0, nullable=False)
    last_checkin_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
class MissionClaim(Base):
    """
    Records that a user has claimed a completed mission's XP reward.
    Mission *definitions* live in code (app/game/missions.py) since
    the MVP has no need for an admin-editable mission list - this
    table only stores the one fact that can't be derived from
    anything else: has this specific mission already been claimed.
    """
    __tablename__ = "mission_claims"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    mission_key = Column(String, nullable=False)
    claimed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
class DailyChallengeClaim(Base):
    """
    Records that a user has claimed today's daily challenge reward.
    One row per (profile_id, challenge_date) - enforced by the router
    checking before inserting, since the challenge itself rotates by
    date (see app/game/daily_challenge.py) rather than being stored.
    """
    __tablename__ = "daily_challenge_claims"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    challenge_date = Column(Date, nullable=False)
    challenge_key = Column(String, nullable=False)
    claimed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
class ChatMessage(Base):
    """
    NEXUS AI chat history - Section 6, the general conversational
    assistant, separate from the situation-card flow. Persisted per
    profile so the conversation survives across sessions/devices
    (once a real "get my world" lookup exists - see the known
    limitation noted earlier about world lookup being local-only).
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
