"""
Simulation Engine - Section 9 & 10 of the Master Spec.

CORE PRINCIPLE: "AI should not be the sole authority for numerical
outcomes." This module owns every numeric state change. The AI layer
only generates narrative text and NEVER decides numbers directly.

Conceptual model: Current State + User Decision + Event + Simulation
Rules -> New State.
"""

from copy import deepcopy
from typing import Any


DEFAULT_STATE = {
    "time_step": 0,
    "resources": {"money": 1000, "energy": 100},
    "skills": {},
    "relationships": {},
    "log": [],
}


def new_world_state(starting_skills: dict[str, int] | None = None) -> dict[str, Any]:
    state = deepcopy(DEFAULT_STATE)
    if starting_skills:
        state["skills"] = dict(starting_skills)
    return state


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def apply_decision(state: dict[str, Any], choice_effects: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    new_state = deepcopy(state)
    applied: dict[str, Any] = {"skills": {}, "resources": {}}

    for skill, delta in choice_effects.get("skills", {}).items():
        current = new_state["skills"].get(skill, 0)
        updated = clamp(current + delta)
        applied["skills"][skill] = updated - current
        new_state["skills"][skill] = updated

    for resource, delta in choice_effects.get("resources", {}).items():
        current = new_state["resources"].get(resource, 0)
        updated = max(0, current + delta)
        applied["resources"][resource] = updated - current
        new_state["resources"][resource] = updated

    new_state["time_step"] += 1

    log_entry = choice_effects.get("log_entry", "A decision was made.")
    new_state["log"].append({"step": new_state["time_step"], "entry": log_entry})

    return new_state, applied


def project_whatif(state: dict[str, Any], hypothetical_effects: dict[str, Any], steps: int = 1) -> dict[str, Any]:
    projected = deepcopy(state)
    for _ in range(steps):
        projected, _ = apply_decision(projected, hypothetical_effects)
    return projected
